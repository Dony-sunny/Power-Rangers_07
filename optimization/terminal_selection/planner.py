from datetime import timedelta
from sqlalchemy import select
from backend.models import Terminal, WaterwayNode, VesselAvailability
from backend.services.timeutils import dt
from feasibility.waterway_constraints.routing import route, lock_wait
from feasibility.terminal_constraints.checks import terminal_checks, next_slot
from feasibility.vessel_constraints.checks import vessel_checks, reserved
from feasibility.compliance.checks import compliance_checks
from feasibility.cargo_constraints.compatibility import compatible
from optimization.multimodal.costs import coordinates, road_distance, water_cost, carbon
from optimization.config import RATES


def node_for(place):
    name = place.casefold()
    return "maradu" if name in {"kochi", "kalamassery", "maradu"} else name


def choose_terminals(
    db, cargo, vessel, exclude_booking_ids=(), availability_override=None
):
    avails = (
        [availability_override]
        if availability_override
        else list(
            db.scalars(
                select(VesselAvailability).where(
                    VesselAvailability.vessel_id == vessel.id,
                    VesselAvailability.active == True,
                )
            )
        )
    )
    if not avails:
        return {
            "passed": False,
            "reasons": ["No active vessel availability."],
            "plans": [],
        }
    origin_coords = coordinates(cargo.origin, cargo.origin_coordinates)
    destination_coords = coordinates(cargo.destination, cargo.destination_coordinates)
    if not origin_coords or not destination_coords:
        return {
            "passed": False,
            "reasons": [
                "Origin/destination coordinates needed for terminal selection."
            ],
            "plans": [],
        }
    terminals = list(db.scalars(select(Terminal)))
    plans, failures = [], []
    for availability in avails:
        base = max(dt(cargo.ready_time), dt(availability.available_from))
        if base >= dt(availability.available_until):
            failures.append("Cargo readiness lies outside vessel availability window.")
            continue
        corridor = route(
            db, node_for(availability.origin), node_for(availability.destination)
        )
        nodes = corridor["nodes"]
        for origin in terminals:
            if origin.node_id not in nodes:
                continue
            if not cargo.first_mile_required and origin.node_id != node_for(
                cargo.origin
            ):
                continue
            orig_node = db.get(WaterwayNode, origin.node_id)
            first_km = (
                road_distance(origin_coords, (orig_node.latitude, orig_node.longitude))
                if cargo.first_mile_required
                else 0
            )
            if first_km > 40:
                continue
            for destination in terminals:
                if destination.node_id not in nodes or nodes.index(
                    destination.node_id
                ) <= nodes.index(origin.node_id):
                    continue
                if not cargo.last_mile_required and destination.node_id != node_for(
                    cargo.destination
                ):
                    continue
                dest_node = db.get(WaterwayNode, destination.node_id)
                last_km = (
                    road_distance(
                        destination_coords, (dest_node.latitude, dest_node.longitude)
                    )
                    if cargo.last_mile_required
                    else 0
                )
                if last_km > 25:
                    continue
                start = next_slot(
                    db,
                    origin.id,
                    base
                    + timedelta(
                        hours=first_km / RATES["road_speed_kmh"] + origin.wait_hours
                    ),
                    exclude_booking_ids=exclude_booking_ids,
                )
                departure = start + timedelta(hours=RATES["handling_hours"])
                path = route(db, origin.node_id, destination.node_id, vessel, departure)
                reasons = list(path["reasons"])
                reasons.extend(terminal_checks(db, cargo, vessel, origin))
                reasons.extend(terminal_checks(db, cargo, vessel, destination))
                elapsed, notices = (
                    lock_wait(db, path["segments"], departure, RATES["water_speed_kmh"])
                    if path["passed"]
                    else (None, [])
                )
                if elapsed is None:
                    reasons.extend(notices)
                    if not reasons:
                        reasons.append("Lock schedule unavailable.")
                water_arrival = departure + timedelta(hours=elapsed or 0)
                unload = next_slot(
                    db,
                    destination.id,
                    water_arrival + timedelta(hours=destination.wait_hours),
                    exclude_booking_ids=exclude_booking_ids,
                )
                eta = unload + timedelta(
                    hours=RATES["handling_hours"] + last_km / RATES["road_speed_kmh"]
                )
                weight, volume, colocated = reserved(
                    db, vessel.id, start, eta, exclude_booking_ids
                )
                reasons.extend(
                    vessel_checks(cargo, vessel, availability, weight, volume)
                )
                if any(not compatible(cargo, other) for other in colocated):
                    reasons.append(
                        "Cargo incompatible with an already reserved co-load."
                    )
                if colocated:
                    reasons.append(
                        "Vessel already assigned to an overlapping voyage; use a single approved pool."
                    )
                reasons.extend(compliance_checks(db, cargo, vessel, departure, eta))
                if eta > dt(cargo.delivery_deadline):
                    reasons.append("Water/terminal schedule misses delivery deadline.")
                if eta > dt(availability.available_until):
                    reasons.append("Voyage exceeds vessel availability window.")
                if reasons:
                    failures.extend(reasons)
                    continue
                waiting = (
                    origin.wait_hours
                    + destination.wait_hours
                    + max(
                        0,
                        (start - base).total_seconds() / 3600
                        - first_km / RATES["road_speed_kmh"]
                        - origin.wait_hours,
                    )
                    + max(
                        0,
                        (unload - water_arrival).total_seconds() / 3600
                        - destination.wait_hours,
                    )
                    + (elapsed or 0)
                    - path["distance_km"] / RATES["water_speed_kmh"]
                )
                breakdown = water_cost(
                    cargo,
                    vessel,
                    origin,
                    destination,
                    first_km,
                    last_km,
                    path["distance_km"],
                    waiting,
                )
                plans.append(
                    {
                        "mode": "HYBRID" if first_km + last_km > 0.05 else "WATER",
                        "feasible": True,
                        "sla": True,
                        "vessel_id": vessel.id,
                        "availability_id": availability.id,
                        "origin_terminal_id": origin.id,
                        "destination_terminal_id": destination.id,
                        "origin_terminal": origin.name,
                        "destination_terminal": destination.name,
                        "departure": departure.isoformat(),
                        "loading_start": start.isoformat(),
                        "unloading_start": unload.isoformat(),
                        "eta": eta.isoformat(),
                        "total_cost": round(sum(breakdown.values()), 2),
                        "breakdown": breakdown,
                        "emissions_kg": round(
                            carbon(cargo.weight_tonnes, first_km + last_km, "road")
                            + carbon(cargo.weight_tonnes, path["distance_km"], "water"),
                            2,
                        ),
                        "hours": round(
                            (eta - dt(cargo.ready_time)).total_seconds() / 3600, 2
                        ),
                        "first_mile_km": round(first_km, 2),
                        "last_mile_km": round(last_km, 2),
                        "road_km": round(first_km + last_km, 2),
                        "water_km": path["distance_km"],
                        "handoffs": 2 + int(first_km > 0.05) + int(last_km > 0.05),
                        "reliability": vessel.reliability_score,
                        "route": path,
                        "lock_notices": notices,
                        "available_capacity": min(
                            availability.capacity_tonnes, vessel.max_capacity_tonnes
                        )
                        - weight,
                        "warnings": [
                            "Cargo volume unknown: final volume verification required before loading."
                        ]
                        if cargo.volume_m3 is None
                        else [],
                    }
                )
    plans.sort(
        key=lambda p: (
            p["total_cost"],
            p["eta"],
            p["origin_terminal_id"],
            p["destination_terminal_id"],
        )
    )
    return {
        "passed": bool(plans),
        "reasons": []
        if plans
        else list(dict.fromkeys(failures))
        or ["No terminal pair fits the cargo, route and service corridor."],
        "plans": plans,
        "best_plan": plans[0] if plans else None,
        "evaluated_pairs": len(plans),
    }
