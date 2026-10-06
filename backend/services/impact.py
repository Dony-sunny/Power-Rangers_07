from statistics import mean, median
from collections import defaultdict
from sqlalchemy import select
from backend.models import *
from backend.services.timeutils import dt
from backend.services.demo_state import flood_enabled
from backend.repositories.common import record
from optimization.terminal_selection.planner import node_for
from optimization.config import EMISSIONS


def calculate_impact(db):
    metrics = []
    delivered = []
    groups = {}
    for metric in db.scalars(select(ImpactMetric)):
        booking = db.get(Booking, metric.booking_id)
        if booking.status in {"CANCELLED", "FAILED", "REPLANNING"}:
            continue
        metrics.append(metric)
        if booking.status == "DELIVERED":
            delivered.append(metric)
        key = booking.pool_id or booking.id
        if metric.tonnes_shifted:
            groups[key] = metric
    demand = defaultdict(
        lambda: {
            "requested_tonnes": 0,
            "booked_tonnes": 0,
            "unserved_tonnes": 0,
            "requests": 0,
        }
    )
    terminal_demand = defaultdict(float)
    unmet = []
    for cargo in db.scalars(select(CargoRequest)):
        key = f"{node_for(cargo.origin)} → {node_for(cargo.destination)}"
        demand[key]["requested_tonnes"] += cargo.weight_tonnes
        demand[key]["requests"] += 1
        valid = db.scalar(
            select(Booking).where(
                Booking.cargo_id == cargo.id,
                Booking.status.not_in(["CANCELLED", "FAILED", "REPLANNING"]),
            )
        )
        if valid:
            demand[key]["booked_tonnes"] += cargo.weight_tonnes
        else:
            demand[key]["unserved_tonnes"] += cargo.weight_tonnes
            unmet.append(
                {
                    "cargo_type": cargo.cargo_type,
                    "weight_tonnes": cargo.weight_tonnes,
                    "origin": cargo.origin,
                    "destination": cargo.destination,
                    "priority": cargo.priority,
                }
            )
        terminal_demand[node_for(cargo.origin)] += cargo.weight_tonnes
    activations = []
    for terminal in db.scalars(select(Terminal)):
        capability = db.scalar(
            select(TerminalCapability).where(
                TerminalCapability.terminal_id == terminal.id
            )
        )
        nearby = terminal_demand[terminal.node_id]
        slots = list(
            db.scalars(
                select(TerminalSlot).where(TerminalSlot.terminal_id == terminal.id)
            )
        )
        active_slots = sum(
            1
            for slot in slots
            if db.get(Booking, slot.booking_id).status not in {"CANCELLED", "FAILED"}
        )
        score = round(
            min(50, nearby / 5)
            + (20 if capability.road_access else 0)
            + (20 if capability.operational_status == "OPEN" else 0)
            + (10 if capability.crane_available else 0),
            1,
        )
        activations.append(
            {
                "terminal": terminal.name,
                "node_id": terminal.node_id,
                "nearby_demand_tonnes": nearby,
                "reserved_slots": active_slots,
                "activation_score": score,
                "capacity_gap_tonnes": max(0, nearby - capability.available_storage),
                "source": "Demo decision-support heuristic; not authoritative infrastructure planning",
            }
        )
    failures = list(
        db.scalars(
            select(MatchRecommendation).where(MatchRecommendation.passed == False)
        )
    )
    unique_failures = {(f.cargo_id, f.vessel_id) for f in failures}
    durations = []
    ontime = 0
    for metric in delivered:
        booking = db.get(Booking, metric.booking_id)
        durations.append(
            (dt(booking.eta) - dt(booking.departure)).total_seconds() / 3600
        )
        cargo = db.get(CargoRequest, booking.cargo_id)
        ontime += dt(booking.eta) <= dt(cargo.delivery_deadline)
    return {
        "tonnes_shifted": round(sum(m.tonnes_shifted for m in metrics), 2),
        "completed_tonnes_shifted": round(sum(m.tonnes_shifted for m in delivered), 2),
        "cost_savings": round(
            sum(m.road_baseline_cost - m.chosen_cost for m in metrics), 2
        ),
        "co2_avoided_kg": round(
            sum(m.road_emissions_kg - m.chosen_emissions_kg for m in metrics), 2
        ),
        "truck_trips_potentially_avoided": sum(m.truck_trips_avoided for m in metrics),
        "utilization_before_pct": round(
            mean(m.utilization_before for m in groups.values()) * 100, 1
        )
        if groups
        else 0,
        "utilization_after_pct": round(
            mean(m.utilization_after for m in groups.values()) * 100, 1
        )
        if groups
        else 0,
        "backhaul_matches": sum(m.empty_return_avoided for m in groups.values()),
        "selected_bookings": len(metrics),
        "completed_bookings": len(delivered),
        "unserved_tonnes": round(sum(c["weight_tonnes"] for c in unmet), 2),
        "unserved_cargo": unmet,
        "corridors": [{"corridor": key, **value} for key, value in demand.items()],
        "terminals": activations,
        "failed_match_count": len(unique_failures),
        "corridor_reliability": {
            "sample_count": len(delivered),
            "median_estimated_journey_hours": round(median(durations), 2)
            if durations
            else None,
            "estimated_on_time_pct": round(ontime / len(delivered) * 100, 1)
            if delivered
            else None,
            "source": "Application plan estimates; insufficient real voyage history for predictive reliability",
        },
        "flood_simulated": flood_enabled(db),
        "emission_factors": EMISSIONS,
        "source": "Aggregated application bookings using synthetic inputs. Selected/confirmed impact is potential; completed impact is separately reported. No certified environmental claims.",
    }


def modal_shift(db):
    from backend.services.planning import compare_modes
    from optimization.matching.engine import match

    results = []
    for cargo in db.scalars(select(CargoRequest)):
        result = match(db, cargo)
        vessel = (
            result["recommendations"][0]["vessel_id"]
            if result["recommendations"]
            else None
        )
        comparison = compare_modes(db, cargo, vessel)
        plan = next(
            (
                p
                for p in comparison["plans"]
                if p["mode"] == comparison["recommended_mode"]
            ),
            None,
        )
        suitability = (
            "HIGH"
            if plan and plan["mode"] != "ROAD" and cargo.consolidation_allowed
            else "MEDIUM"
            if any(p["feasible"] and p["mode"] != "ROAD" for p in comparison["plans"])
            else "LOW"
        )
        results.append(
            {
                "cargo_type": cargo.cargo_type,
                "weight_tonnes": cargo.weight_tonnes,
                "origin": cargo.origin,
                "destination": cargo.destination,
                "suitability": suitability,
                "recommended_mode": comparison["recommended_mode"],
                "reason": comparison["explanation"],
            }
        )
    return {
        "rows": results,
        "source": "Deterministic modal-shift evaluation of synthetic platform demand; not a trained ML model.",
    }
