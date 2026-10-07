"""A common water schedule, individual road legs, pinned tariffs and full checks."""
from datetime import timedelta
from types import SimpleNamespace
from sqlalchemy import select
from fastapi import HTTPException
from backend.models import *
from backend.repositories.common import record
from backend.services.timeutils import dt
from backend.services.terminal_resources import apply_group_requirements, choose_resources
from feasibility.engine import check_feasibility
from feasibility.terminal_constraints.checks import next_slot, terminal_checks
from feasibility.vessel_constraints.checks import reserved, vessel_checks
from feasibility.compliance.checks import compliance_checks
from feasibility.cargo_constraints.compatibility import compatible
from feasibility.waterway_constraints.routing import route, lock_wait
from optimization.multimodal.costs import coordinates, road_plan, carbon, road_distance
from optimization.multimodal.trip_costs import (TERMS, minor, product, rupees, allocate,
                                               trips, truck_charge, handling_hours, sailing_economics)
from optimization.config import RATES


def loaded_cargo(db, cargo):
    data = record(cargo) if isinstance(cargo, CargoRequest) else vars(cargo).copy()
    profile = db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == cargo.id))
    if profile:
        for key, value in record(profile).items():
            if key not in {"id", "cargo_id"}:
                data.setdefault(key, value)
    return SimpleNamespace(**data)


def rate_card(db, terminal_id, card_id=None):
    card = db.get(TerminalRateCard, card_id) if card_id else db.scalar(select(TerminalRateCard).where(
        TerminalRateCard.terminal_id == terminal_id).order_by(TerminalRateCard.version.desc()))
    if not card or card.terminal_id != terminal_id:
        raise HTTPException(409, "Accepted terminal rate card is unavailable.")
    return card


def handling_slot(db, terminal, card, earliest, duration, exclusions, cargo, vessel):
    """Keep a complete handling job inside its pinned card's daily operating window."""
    opening, closing = card.terms["operating_hours"]
    def hour(value):
        h, m = map(int, value.split(":"))
        return h + m / 60
    first, last = hour(opening), hour(closing)
    if not 0 <= first < 24 or not 0 < last <= 24:
        raise HTTPException(409, "Terminal card operating hours are invalid.")
    daily_hours = (last - first) if last > first else 24 - first + last
    if duration > daily_hours:
        raise HTTPException(409, "Handling duration exceeds the terminal's operating window.")
    candidate = earliest
    for _ in range(7):
        midnight = candidate.replace(hour=0, minute=0, second=0, microsecond=0)
        start = midnight + timedelta(hours=first)
        end = midnight + timedelta(hours=last if last > first else last + 24)
        if last <= first and candidate < start and candidate <= midnight + timedelta(hours=last):
            start -= timedelta(days=1)
            end -= timedelta(days=1)
        if candidate + timedelta(hours=duration) > end:
            candidate = start + timedelta(days=1)
            continue
        candidate = max(candidate, start)
        scheduled = next_slot(db, terminal.id, candidate, duration, exclusions, cargo, vessel)
        if scheduled + timedelta(hours=duration) <= end:
            return scheduled
        candidate = scheduled
    raise HTTPException(409, "No complete terminal handling window is available within seven days.")


def build_plan(db, original_cargos, vessel, exclusions=(), pinned_cards=None, pinned_availability_id=None, not_before=None):
    if pinned_availability_id:
        listing = db.get(VesselAvailability, pinned_availability_id)
        if not listing or listing.vessel_id != vessel.id:
            raise HTTPException(404, "Boat availability listing not found.")
    cargos = [loaded_cargo(db, item) for item in original_cargos]
    if any(item.volume_m3 is None for item in cargos):
        raise HTTPException(409, "Confirm every cargo volume before reserving a departure.")
    if any(not hasattr(item, "heaviest_piece_tonnes") for item in cargos):
        raise HTTPException(409, "Review the heaviest piece and load dimensions before reserving.")
    if len(cargos) > 1 and any(not item.consolidation_allowed for item in cargos):
        raise HTTPException(409, "A cargo owner has prohibited consolidation.")
    if any(not compatible(a, b) for i, a in enumerate(cargos) for b in cargos[i + 1:]):
        raise HTTPException(409, "Cargo categories cannot share this departure.")
    options = []
    for item in cargos:
        result = check_feasibility(db, item, vessel, exclude_booking_ids=exclusions,
            availability_override=db.get(VesselAvailability, pinned_availability_id) if pinned_availability_id else None)
        if not result["passed"]:
            raise HTTPException(409, {"message": "Cargo cannot use this vessel.", "reasons": result["reasons"]})
        options.append(result["terminal_options"])
    common = set((p["origin_terminal_id"], p["destination_terminal_id"], p["availability_id"]) for p in options[0])
    for member_options in options[1:]:
        common &= {(p["origin_terminal_id"], p["destination_terminal_id"], p["availability_id"]) for p in member_options}
    failures, feasible = [], []
    for origin_id, destination_id, availability_id in sorted(common):
        if pinned_cards and {origin_id, destination_id} != set(pinned_cards):
            continue
        origin, destination = db.get(Terminal, origin_id), db.get(Terminal, destination_id)
        availability = db.get(VesselAvailability, availability_id)
        cards = [rate_card(db, origin_id, (pinned_cards or {}).get(origin_id)), rate_card(db, destination_id, (pinned_cards or {}).get(destination_id))]
        selected = [next(p for p in opts if (p["origin_terminal_id"], p["destination_terminal_id"], p["availability_id"]) == (origin_id, destination_id, availability_id)) for opts in options]
        merged = SimpleNamespace(**vars(cargos[0]))
        merged.weight_tonnes = sum(c.weight_tonnes for c in cargos)
        merged.volume_m3 = sum(c.volume_m3 for c in cargos)
        apply_group_requirements(merged, cargos)
        reasons = []
        for item in cargos:
            for place, supplied, terminal, required, label in [(item.origin, item.origin_coordinates, origin, item.first_mile_required, "pickup"), (item.destination, item.destination_coordinates, destination, item.last_mile_required, "final delivery")]:
                node = db.get(WaterwayNode, terminal.node_id)
                if not required and road_distance(coordinates(place, supplied), (node.latitude, node.longitude)) > .05:
                    reasons.append(f"{item.id}: {label} point is away from the terminal; request the connecting truck or choose terminal handover.")
            for terminal, card in zip([origin, destination], cards):
                reasons += terminal_checks(db, item, vessel, terminal)
                if item.cargo_type not in card.terms["cargo_categories"] or item.packaging not in card.terms["packaging"]:
                    reasons.append(f"{terminal.name}: rate card does not cover this cargo/packaging.")
                cap = db.scalar(select(TerminalCapability).where(TerminalCapability.terminal_id == terminal.id))
                lift = cap.crane_capacity if item.cargo_type in {"steel", "construction"} or item.heaviest_piece_tonnes > cap.forklift_capacity else cap.forklift_capacity
                if item.heaviest_piece_tonnes > lift or item.heaviest_piece_tonnes > 20:
                    reasons.append(f"{terminal.name}: indivisible {item.heaviest_piece_tonnes:g} t piece exceeds {lift:g} t lift/truck limit.")
                if item.heaviest_piece_tonnes > cap.forklift_capacity:
                    merged.needs_crane = True
            if item.unit_length_m > 6 or item.unit_width_m > 2.4 or item.unit_height_m > 2.5:
                reasons.append("Indivisible load dimensions exceed the configured truck envelope.")
        reasons += terminal_checks(db, merged, vessel, origin) + terminal_checks(db, merged, vessel, destination)
        pickup_ready = max(max(dt(c.ready_time), dt(availability.available_from)) + timedelta(hours=p["first_mile_km"] / RATES["road_speed_kmh"] + (.25 if c.first_mile_required else 0)) for c, p in zip(cargos, selected))
        load_hours, unload_hours = [handling_hours(merged.weight_tonnes, card.terms) for card in cards]
        try:
            start = handling_slot(db, origin, cards[0], max(pickup_ready + timedelta(hours=origin.wait_hours), dt(not_before) - timedelta(hours=load_hours)) if not_before else pickup_ready + timedelta(hours=origin.wait_hours), load_hours, exclusions, merged, vessel)
        except HTTPException as error:
            failures.append(str(error.detail))
            continue
        departure = start + timedelta(hours=load_hours)
        path = route(db, origin.node_id, destination.node_id, vessel, departure)
        reasons += path["reasons"]
        elapsed, notices = lock_wait(db, path["segments"], departure, RATES["water_speed_kmh"]) if path["passed"] else (None, [])
        if elapsed is None:
            reasons += notices or ["Water route or lock window is unavailable."]
        arrival = departure + timedelta(hours=elapsed or 0)
        try:
            unload = handling_slot(db, destination, cards[1], arrival + timedelta(hours=destination.wait_hours), unload_hours, exclusions, merged, vessel)
        except HTTPException as error:
            failures.append(str(error.detail))
            continue
        end = unload + timedelta(hours=unload_hours)
        occupied_weight, occupied_volume, other = reserved(db, vessel.id, start, end, exclusions)
        reasons += vessel_checks(merged, vessel, availability, occupied_weight, occupied_volume)
        if other:
            reasons.append("Vessel belongs to an overlapping departure.")
        if end > dt(availability.available_until):
            reasons.append("Shared handling and water interval exceed vessel availability.")
        for terminal_id, window_start, window_end in [(origin_id, start, departure), (destination_id, unload, end)]:
            _, conflicts = choose_resources(db, terminal_id, merged, vessel, window_start, window_end, exclusions)
            reasons += conflicts
        fixed = {"sailing_fixed": minor(TERMS["sailing_sale_fixed"]), "origin_handling_setup": cards[0].terms["setup_minor"], "destination_handling_setup": cards[1].terms["setup_minor"]}
        shares = {key: allocate(value, [c.weight_tonnes for c in cargos]) for key, value in fixed.items()}
        waiting = max(0, (start - pickup_ready).total_seconds() / 3600) + max(0, (unload - arrival).total_seconds() / 3600) + max(0, (elapsed or 0) - path["distance_km"] / RATES["water_speed_kmh"])
        member_plans = []
        for i, (item, original) in enumerate(zip(cargos, selected)):
            eta = end + timedelta(hours=original["last_mile_km"] / RATES["road_speed_kmh"] + (.25 if item.last_mile_required else 0))
            natural_eta = eta
            if getattr(item, "receiving_from", None):
                eta = max(eta, dt(item.receiving_from))
            if eta > dt(item.delivery_deadline) or (getattr(item, "receiving_until", None) and eta > dt(item.receiving_until)):
                reasons.append(f"{item.id}: individual door arrival misses receiving/deadline window.")
            reasons += compliance_checks(db, item, vessel, departure, end)
            breakdown = {key: values[i] for key, values in shares.items()}
            breakdown.update({"first_mile_truck": truck_charge(item, original["first_mile_km"], True, item.first_mile_required), "last_mile_truck": truck_charge(item, original["last_mile_km"], True, item.last_mile_required),
                "water_freight": product(item.weight_tonnes, path["distance_km"], vessel.rate_per_tonne_km),
                "origin_handling": product(item.weight_tonnes, cards[0].terms["per_tonne_minor"] / 100),
                "destination_handling": product(item.weight_tonnes, cards[1].terms["per_tonne_minor"] / 100),
                "storage_waiting": product(item.weight_tonnes, waiting, cards[0].terms["storage_per_tonne_hour_minor"] / 100)})
            pickup_arrival = dt(item.ready_time) + timedelta(hours=original["first_mile_km"] / RATES["road_speed_kmh"] + .25)
            pickup_wait = max(0, (departure - pickup_arrival).total_seconds() / 3600 - TERMS["truck_wait_allowance_hours"])
            receiver_wait = max(0, (eta - natural_eta).total_seconds() / 3600 - TERMS["truck_wait_allowance_hours"])
            breakdown["pickup_truck_waiting"] = product(trips(item), pickup_wait, TERMS["truck_wait_per_hour"]) if item.first_mile_required else 0
            breakdown["delivery_truck_waiting"] = product(trips(item), receiver_wait, TERMS["truck_wait_per_hour"]) if item.last_mile_required else 0
            total = sum(breakdown.values())
            if item.budget and rupees(total) > item.budget:
                reasons.append(f"{item.id}: full delivered quote exceeds the cargo budget.")
            member_plans.append({**original, "mode": "HYBRID" if item.first_mile_required or item.last_mile_required else "WATER", "cargo_id": item.id, "loading_start": start.isoformat(), "departure": departure.isoformat(), "unloading_start": unload.isoformat(), "water_end": end.isoformat(), "eta": eta.isoformat(),
                "pickup_start": item.ready_time, "total_minor": total, "total_cost": rupees(total), "breakdown_minor": breakdown, "breakdown": {k: rupees(v) for k, v in breakdown.items()},
                "first_mile_trips": trips(item) if item.first_mile_required else 0, "last_mile_trips": trips(item) if item.last_mile_required else 0,
                "rate_card_ids": [c.id for c in cards], "tariff": TERMS.copy(), "road_baseline": road_plan(item), "route": path,
                "hours": round((eta - dt(item.ready_time)).total_seconds() / 3600, 2), "source": "SIMULATED", "receiving_window": [getattr(item, "receiving_from", None), getattr(item, "receiving_until", None)]})
        if reasons:
            failures += reasons
            continue
        economics = sailing_economics(merged.weight_tonnes, path["distance_km"], vessel.rate_per_tonne_km)
        water_revenue = sum(p["breakdown_minor"]["sailing_fixed"] + p["breakdown_minor"]["water_freight"] for p in member_plans)
        total_revenue = sum(p["total_minor"] for p in member_plans)
        pass_through = total_revenue - water_revenue
        economics.update({"water_revenue_minor": water_revenue, "water_operating_minor": economics["operating_cost_minor"],
            "provider_pass_through_minor": pass_through, "revenue_minor": total_revenue, "operating_cost_minor": economics["operating_cost_minor"] + pass_through,
            "contribution_minor": water_revenue - economics["operating_cost_minor"], "covers_modeled_costs": water_revenue >= economics["operating_cost_minor"],
            "basis": "Complete accepted delivery revenue minus truck/terminal pass-through payables and modeled water operating allowances. Shared terminal setup is retained after cancellation. Excludes tax, finance, platform overhead and unbooked return revenue; not audited net profit."})
        feasible.append({"vessel_id": vessel.id, "availability_id": availability.id, "origin_terminal_id": origin_id, "destination_terminal_id": destination_id,
            "loading_start": start.isoformat(), "departure": departure.isoformat(), "unloading_start": unload.isoformat(), "water_end": end.isoformat(),
            "load_hours": load_hours, "unload_hours": unload_hours, "weight_tonnes": merged.weight_tonnes, "volume_m3": merged.volume_m3,
            "utilization": merged.weight_tonnes / vessel.max_capacity_tonnes, "members": member_plans, "economics": economics, "rate_card_ids": [c.id for c in cards],
            "required_crane": getattr(merged, "needs_crane", False), "required_forklift": getattr(merged, "needs_forklift", False), "route": path, "tariff": TERMS.copy(),
            "commitment_policy": "PROVISIONAL until owner approvals and all simulated providers accept; then COMMITTED_DEMO. Remaining accepted prices survive member cancellation.", "source": "SIMULATED"})
    if not feasible:
        raise HTTPException(409, {"message": "No common dated departure meets every constraint.", "reasons": list(dict.fromkeys(failures)) or ["Loads need different terminal pairs/availability windows."]})
    if not_before:
        for plan in feasible:
            plan["not_before"] = dt(not_before).isoformat()
    return min(feasible, key=lambda p: (sum(m["total_minor"] for m in p["members"]), p["departure"]))
