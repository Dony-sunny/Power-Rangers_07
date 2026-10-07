from collections import defaultdict
from statistics import median, mean
from datetime import timedelta
from types import SimpleNamespace
from sqlalchemy import select
from backend.models import *
from backend.repositories.common import uid, record
from backend.services.timeutils import dt, utcnow
from optimization.terminal_selection.planner import node_for


def classify_failure(reasons):
    text = " ".join(reasons).lower()
    result = []
    if "capacity" in text or "volume" in text:
        result.append("NO_CAPACITY")
    if any(
        word in text
        for word in ["depth", "draft", "bridge", "route", "width", "closed segment"]
    ):
        result.append("NO_FEASIBLE_ROUTE")
    if any(
        word in text for word in ["terminal", "crane", "forklift", "storage", "jetty"]
    ):
        result.append("NO_TERMINAL_CAPABILITY")
    if any(word in text for word in ["availability", "window", "schedule", "lock"]):
        result.append("SCHEDULE_MISMATCH")
    if any(word in text for word in ["deadline", "sla"]):
        result.append("DEADLINE_IMPOSSIBLE")
    return result or ["NO_VESSEL"]


def record_search(db, cargo, candidates, rejected):
    reasons = (
        classify_failure(
            [reason for item in rejected for reason in item["feasibility"]["reasons"]]
        )
        if not candidates
        else []
    )
    db.add(
        DemandSearch(
            id=uid("demand-search"),
            cargo_id=cargo.id,
            outcome="MATCHED" if candidates else reasons[0],
            reasons=reasons,
        )
    )


def failed_demand(db, organization_ids=None):
    from optimization.matching.engine import match

    corridors = defaultdict(
        lambda: {
            "tonnes": 0,
            "cargo_count": 0,
            "search_frequency": 0,
            "reasons": defaultdict(lambda: {"tonnes": 0, "requests": 0}),
        }
    )
    rows = []
    for cargo in db.scalars(select(CargoRequest)):
        if organization_ids is not None and cargo.organization_id not in organization_ids:
            continue
        if db.scalar(
            select(Booking).where(
                Booking.cargo_id == cargo.id,
                Booking.status.not_in(["CANCELLED", "FAILED", "REPLANNING"]),
            )
        ):
            continue
        searches = list(
            db.scalars(
                select(DemandSearch)
                .where(DemandSearch.cargo_id == cargo.id)
                .order_by(DemandSearch.created_at)
            )
        )
        if searches and searches[-1].outcome == "PRICE_REJECTED":
            reasons = ["PRICE_REJECTED"]
        else:
            matched = match(db, cargo)
            reasons = (
                []
                if matched["recommendations"]
                else classify_failure(
                    [
                        reason
                        for rejected in matched["rejected"]
                        for reason in rejected["feasibility"]["reasons"]
                    ]
                )
            )
        corridor = f"{node_for(cargo.origin)} → {node_for(cargo.destination)}"
        bucket = corridors[corridor]
        bucket["tonnes"] += cargo.weight_tonnes
        bucket["cargo_count"] += 1
        bucket["search_frequency"] += len(searches)
        for reason in reasons:
            bucket["reasons"][reason]["tonnes"] += cargo.weight_tonnes
            bucket["reasons"][reason]["requests"] += 1
        rows.append(
            {
                "cargo_id": cargo.id,
                "cargo_type": cargo.cargo_type,
                "tonnes": cargo.weight_tonnes,
                "corridor": corridor,
                "reasons": reasons or ["UNBOOKED_FEASIBLE"],
                "search_count": len(searches),
            }
        )
    return {
        "corridors": [
            {"corridor": key, **value, "reasons": dict(value["reasons"])}
            for key, value in corridors.items()
        ],
        "rows": rows,
        "unserved_tonnes": round(sum(row["tonnes"] for row in rows), 2),
        "source": "Latest current feasibility/explicit price rejection. Tonnage counts unique requests; frequency counts search events. Multiple reasons can describe the same request.",
    }


def corridor_reliability(db):
    groups = defaultdict(dict)
    for booking in db.scalars(select(Booking)):
        cargo = db.get(CargoRequest, booking.cargo_id)
        corridor = f"{node_for(cargo.origin)} → {node_for(cargo.destination)}"
        capacity = db.scalar(
            select(ScheduledCapacityBooking).where(
                ScheduledCapacityBooking.booking_id == booking.id
            )
        )
        key = booking.pool_id or (capacity.service_id if capacity else booking.id)
        groups[corridor].setdefault(key, []).append(booking)
    rows = []
    for corridor, voyages in groups.items():
        durations = []
        waits = []
        ontime = completed = cancelled = recoveries = disruptions = 0
        for bookings in voyages.values():
            if all(b.status == "CANCELLED" for b in bookings):
                cancelled += 1
            event_sets = []
            for booking in bookings:
                shipment = db.scalar(
                    select(Shipment).where(Shipment.booking_id == booking.id)
                )
                events = (
                    list(
                        db.scalars(
                            select(TrackingEvent)
                            .where(TrackingEvent.shipment_id == shipment.id)
                            .order_by(TrackingEvent.timestamp)
                        )
                    )
                    if shipment
                    else []
                )
                event_sets.append((booking, events))
            if all(booking.status == "DELIVERED" for booking in bookings):
                completed += 1
                first = [
                    dt(e.timestamp)
                    for _, events in event_sets
                    for e in events
                    if e.status == "IN_TRANSIT"
                ]
                last = [
                    dt(
                        next(
                            (e.timestamp for e in events if e.status == "UNLOADING"),
                            next(
                                (
                                    e.timestamp
                                    for e in events
                                    if e.status == "DELIVERED"
                                ),
                                "",
                            ),
                        )
                    )
                    for _, events in event_sets
                    if any(e.status in {"UNLOADING", "DELIVERED"} for e in events)
                ]
                if first and last:
                    durations.append(
                        max(0, (max(last) - min(first)).total_seconds() / 3600)
                    )
                delivery = [
                    (
                        booking,
                        next(
                            (e for e in reversed(events) if e.status == "DELIVERED"),
                            None,
                        ),
                    )
                    for booking, events in event_sets
                ]
                if all(
                    event
                    and dt(event.timestamp)
                    <= dt(db.get(CargoRequest, booking.cargo_id).delivery_deadline)
                    for booking, event in delivery
                ):
                    ontime += 1
                for booking, events in event_sets:
                    loading = next((e for e in events if e.status == "LOADING"), None)
                    if loading and booking.plan_snapshot.get("loading_start"):
                        waits.append(
                            max(
                                0,
                                (
                                    dt(loading.timestamp)
                                    - dt(booking.plan_snapshot["loading_start"])
                                ).total_seconds()
                                / 3600,
                            )
                        )
            incidents = [
                item
                for booking in bookings
                for item in db.scalars(
                    select(DisruptionRecord).where(
                        DisruptionRecord.booking_id == booking.id
                    )
                )
            ]
            recoveries += any(
                any(e.description.startswith("Recovery explicitly") for e in events)
                for _, events in event_sets
            )
            disruptions += any(
                item.kind
                in {"ROUTE_CLOSED", "TERMINAL_CLOSED", "EQUIPMENT_UNAVAILABLE"}
                for item in incidents
            )
        total = len(voyages)
        sample = completed
        ontime_rate = ontime / sample * 100 if sample else None
        score = (
            round(
                max(
                    0,
                    min(
                        100,
                        (ontime_rate or 0) * 0.7
                        + (1 - cancelled / max(1, total)) * 20
                        + (1 - disruptions / max(1, total)) * 10,
                    ),
                ),
                1,
            )
            if sample >= 5
            else None
        )
        rows.append(
            {
                "corridor": corridor,
                "completed_trips": completed,
                "sample_size": sample,
                "recorded_transit_samples": len(durations),
                "median_transit_hours": round(median(durations), 3)
                if durations
                else None,
                "average_terminal_wait_hours": round(mean(waits), 3) if waits else None,
                "on_time_pct": round(ontime_rate, 1)
                if ontime_rate is not None
                else None,
                "cancellation_pct": round(cancelled / max(1, total) * 100, 1),
                "recovery_frequency_pct": round(recoveries / max(1, total) * 100, 1),
                "route_disruption_pct": round(disruptions / max(1, total) * 100, 1),
                "reliability_score": score,
                "history_status": "Insufficient history"
                if sample < 5
                else "Descriptive demo history",
                "source": "Recorded application milestones. Fast demo transitions are not representative voyage durations. Score is descriptive, not predictive ML.",
            }
        )
    return {"corridors": rows, "minimum_score_sample": 5}


def rate_benchmark(db, cargo, current_total=None, days=90):
    weight = cargo.weight_tonnes
    low, high = (0, 50) if weight < 50 else (50, 100) if weight <= 100 else (100, 5000)
    klass = (
        "construction"
        if cargo.cargo_type in {"cement", "steel", "construction"}
        else cargo.cargo_type
    )
    origin = node_for(cargo.origin)
    destination = node_for(cargo.destination)
    samples = []
    sources = set()
    for item in db.scalars(select(FreightRateObservation)):
        if (
            item.origin == origin
            and item.destination == destination
            and item.cargo_class == klass
            and low <= item.weight_tonnes <= high
            and utcnow() - timedelta(days=days) <= dt(item.observed_at) <= utcnow()
        ):
            samples.append(item.rate_per_tonne)
            sources.add(item.source)
    for booking in db.scalars(
        select(Booking).where(
            Booking.status.not_in(["CANCELLED", "FAILED", "REPLANNING"])
        )
    ):
        other = db.get(CargoRequest, booking.cargo_id)
        other_class = (
            "construction"
            if other.cargo_type in {"cement", "steel", "construction"}
            else other.cargo_type
        )
        if (
            node_for(other.origin) == origin
            and node_for(other.destination) == destination
            and other_class == klass
            and low <= other.weight_tonnes <= high
            and utcnow() - timedelta(days=days) <= dt(booking.created_at) <= utcnow()
        ):
            samples.append(booking.total_cost / other.weight_tonnes)
            sources.add("Application accepted demo booking")
    rate = current_total / weight if current_total is not None else None
    sufficient = len(samples) >= 3
    floor = min(samples) if sufficient else None
    ceiling = max(samples) if sufficient else None
    status = (
        "INSUFFICIENT_HISTORY"
        if not sufficient
        else "BELOW_RANGE"
        if rate is not None and rate < floor
        else "ABOVE_RANGE"
        if rate is not None and rate > ceiling
        else "WITHIN_RANGE"
        if rate is not None
        else "NO_CURRENT_QUOTE"
    )
    return {
        "corridor": f"{origin} → {destination}",
        "cargo_class": klass,
        "weight_band_tonnes": [low, high],
        "lookback_days": days,
        "sample_size": len(samples),
        "range_per_tonne": [round(floor, 2), round(ceiling, 2)] if sufficient else None,
        "current_rate_per_tonne": round(rate, 2) if rate is not None else None,
        "status": status,
        "sources": sorted(sources),
        "source": "Comparable prototype delivered-cost rates, not sourced industry market rates. Small samples do not expose a range.",
    }


def seed_rate_history(db):
    if db.scalar(select(FreightRateObservation)):
        return
    from backend.services.planning import compare_modes

    cargo = db.get(CargoRequest, "hero-cargo")
    if not cargo:
        return
    plan = next(
        item
        for item in compare_modes(db, cargo, "vembanad")["plans"]
        if item["mode"] == "HYBRID"
    )
    if not plan["feasible"]:
        return
    base = plan["total_cost"] / cargo.weight_tonnes
    for index, multiplier in enumerate([0.94, 0.97, 1.0, 1.03, 1.06]):
        db.add(
            FreightRateObservation(
                id=f"demo-rate-{index}",
                origin="maradu",
                destination="alappuzha",
                cargo_class="construction",
                weight_tonnes=80,
                rate_per_tonne=round(base * multiplier, 2),
                observed_at=(utcnow() - timedelta(days=7 * (index + 1))).isoformat(),
                source="Synthetic demo rate history from configured cost model × disclosed 0.94–1.06 multipliers",
            )
        )
    db.flush()


def historical_modal_shift(db, rows):
    from data.seed.network import tomorrow
    from backend.services.planning import compare_modes
    from optimization.matching.engine import match

    results = []
    valid = [row for row in rows if row["valid"]]
    frequencies = defaultdict(int)
    for row in valid:
        fields = row["fields"]
        frequencies[(node_for(fields["origin"]), node_for(fields["destination"]))] += 1
    for row in valid:
        fields = row["fields"]
        window = dt(fields["delivery_deadline"]) - dt(fields["ready_time"])
        cargo = SimpleNamespace(
            id=f"historical-row-{row['row']}",
            organization_id="analysis-only",
            status="POSTED",
            **fields,
        )
        cargo.ready_time = tomorrow().isoformat()
        cargo.delivery_deadline = (tomorrow() + window).isoformat()
        matched = match(db, cargo)
        comparison = compare_modes(
            db,
            cargo,
            matched["recommendations"][0]["vessel_id"]
            if matched["recommendations"]
            else None,
        )
        road = comparison["plans"][0]
        water = next(
            (
                plan
                for plan in sorted(
                    [
                        p
                        for p in comparison["plans"]
                        if p["feasible"] and p["mode"] != "ROAD"
                    ],
                    key=lambda p: p["total_cost"],
                )
            ),
            None,
        )
        reasons = []
        if cargo.weight_tonnes >= 20:
            reasons.append("High tonnage")
        if window.total_seconds() / 3600 >= 12:
            reasons.append("Non-urgent delivery window")
        if frequencies[(node_for(cargo.origin), node_for(cargo.destination))] >= 2:
            reasons.append("Repeated corridor demand in uploaded sample")
        if water:
            reasons.extend(
                [
                    "Cargo/vessel/terminal/route compatibility passed",
                    f"Connecting road distance: {water.get('road_km', 0):g} km",
                ]
            )
        else:
            reasons.append("No feasible water plan against current configured snapshot")
        saving = (road.get("total_cost") or 0) - water["total_cost"] if water else 0
        suitability = (
            "HIGH"
            if water
            and saving > 0
            and cargo.weight_tonnes >= 20
            and window.total_seconds() >= 12 * 3600
            else "MEDIUM"
            if water
            else "LOW"
        )
        results.append(
            {
                "row": row["row"],
                "reference": row.get("reference", ""),
                "weight_tonnes": cargo.weight_tonnes,
                "origin": cargo.origin,
                "destination": cargo.destination,
                "suitability": suitability,
                "reasons": reasons,
                "potential_cost_difference": round(saving, 2),
                "potential_emissions_difference_kg": round(
                    (road.get("emissions_kg") or 0) - water["emissions_kg"], 2
                )
                if water
                else 0,
                "truck_movements_estimate": __import__("math").ceil(
                    cargo.weight_tonnes / 20
                )
                if water
                else 0,
            }
        )
    candidates = [row for row in results if row["suitability"] != "LOW"]
    return {
        "label": "POTENTIAL MODAL-SHIFT OPPORTUNITY",
        "rows": results,
        "invalid_rows": [row for row in rows if not row["valid"]],
        "total_shipments_analyzed": len(results),
        "candidate_shipments": len(candidates),
        "candidate_tonnes": round(sum(row["weight_tonnes"] for row in candidates), 2),
        "estimated_cost_difference": round(
            sum(row["potential_cost_difference"] for row in candidates), 2
        ),
        "estimated_truck_movements": sum(
            row["truck_movements_estimate"] for row in candidates
        ),
        "estimated_co2_difference_kg": round(
            sum(row["potential_emissions_difference_kg"] for row in candidates), 2
        ),
        "source": "Historical rows replayed into tomorrow’s demo availability, preserving original time slack. Feasibility reflects current configured synthetic snapshot, not historical navigation conditions or guaranteed conversion.",
    }
