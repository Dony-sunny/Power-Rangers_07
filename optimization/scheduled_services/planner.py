from datetime import timedelta
from sqlalchemy import select
from fastapi import HTTPException
from backend.models import (
    ScheduledServiceStop,
    ScheduledCapacityBooking,
    Terminal,
    CargoRequest,
    Booking,
    Vessel,
    VesselAvailability,
)
from backend.services.timeutils import dt
from backend.repositories.common import record
from optimization.terminal_selection.planner import node_for
from feasibility.vessel_constraints.checks import ACTIVE_BOOKING_STATES
from feasibility.compliance.checks import compliance_checks


def stop_pair(db, service, cargo):
    stops = list(
        db.scalars(
            select(ScheduledServiceStop)
            .where(ScheduledServiceStop.service_id == service.id)
            .order_by(ScheduledServiceStop.sequence)
        )
    )
    origin = next(
        (
            stop
            for stop in stops
            if db.get(Terminal, stop.terminal_id).node_id == node_for(cargo.origin)
        ),
        None,
    )
    destination = next(
        (
            stop
            for stop in stops
            if db.get(Terminal, stop.terminal_id).node_id == node_for(cargo.destination)
        ),
        None,
    )
    if (
        not service.active
        or not origin
        or not destination
        or origin.sequence >= destination.sequence
    ):
        raise HTTPException(
            409, "Cargo does not fit this active scheduled service corridor."
        )
    if dt(cargo.ready_time) > dt(origin.departure) - timedelta(hours=0.75):
        raise HTTPException(409, "Cargo is not ready before scheduled loading.")
    if dt(destination.arrival) + timedelta(hours=0.75) > dt(cargo.delivery_deadline):
        raise HTTPException(409, "Scheduled service misses the delivery deadline.")
    return origin, destination


def segment_usage(db, service, exclude_contract=None):
    stops = list(
        db.scalars(
            select(ScheduledServiceStop)
            .where(ScheduledServiceStop.service_id == service.id)
            .order_by(ScheduledServiceStop.sequence)
        )
    )
    used = {stop.sequence: 0.0 for stop in stops[:-1]}
    for reservation in db.scalars(
        select(ScheduledCapacityBooking).where(
            ScheduledCapacityBooking.service_id == service.id
        )
    ):
        booking = db.get(Booking, reservation.booking_id)
        if not booking or booking.status in {"CANCELLED", "FAILED"}:
            continue
        for sequence in used:
            if reservation.start_sequence <= sequence < reservation.end_sequence:
                used[sequence] += reservation.weight_tonnes
    from backend.services.recurring import held_capacity

    for sequence in used:
        used[sequence] += held_capacity(db, service.id, sequence, exclude_contract)
    return used


def validate_capacity(db, service, cargo, contract_id=None, actor=None):
    origin, destination = stop_pair(db, service, cargo)
    if contract_id:
        from backend.models import CapacityContract, ContractReservation, ContractDraw

        contract = db.get(CapacityContract, contract_id)
        reservation = db.scalar(
            select(ContractReservation).where(
                ContractReservation.contract_id == contract_id,
                ContractReservation.service_id == service.id,
            )
        )
        if (
            not contract
            or not actor
            or contract.organization_id != actor.organization_id
            or contract.status != "ACTIVE"
            or not reservation
        ):
            raise HTTPException(404, "Contract capacity not found.")
        drawn = sum(
            item.tonnes
            for item in db.scalars(
                select(ContractDraw).where(
                    ContractDraw.contract_id == contract_id,
                    ContractDraw.service_id == service.id,
                )
            )
            if db.get(Booking, item.booking_id).status not in {"CANCELLED", "FAILED"}
        )
        if (
            cargo.weight_tonnes + drawn > reservation.tonnes
            or origin.sequence < contract.start_sequence
            or destination.sequence > contract.end_sequence
        ):
            raise HTTPException(
                409, "Cargo exceeds reserved contract capacity or stop coverage."
            )
    from backend.services.recurring import segment_limit

    if any(
        used + cargo.weight_tonnes > segment_limit(db, service, seq) + 1e-9
        for seq, used in segment_usage(db, service, contract_id).items()
        if origin.sequence <= seq < destination.sequence
    ):
        raise HTTPException(
            409, "Scheduled capacity would exceed a service segment limit."
        )
    return origin, destination


def service_plan(db, service, cargo, plan):
    origin, destination = stop_pair(db, service, cargo)
    if (
        plan["origin_terminal_id"] != origin.terminal_id
        or plan["destination_terminal_id"] != destination.terminal_id
    ):
        raise HTTPException(
            409,
            "Scheduled service uses different terminals from the selected feasible plan.",
        )
    departure = dt(origin.departure)
    eta = dt(destination.arrival) + timedelta(
        hours=0.75 + plan.get("last_mile_km", 0) / 32
    )
    if dt(cargo.ready_time) + timedelta(
        hours=plan.get("first_mile_km", 0) / 32 + 0.75
    ) > departure or eta > dt(cargo.delivery_deadline):
        raise HTTPException(
            409, "First/last-mile connection cannot fit the scheduled stop times."
        )
    vessel = db.get(Vessel, service.vessel_id)
    from feasibility.waterway_constraints.routing import route, lock_wait
    from feasibility.terminal_constraints.checks import terminal_checks

    origin_terminal = db.get(Terminal, origin.terminal_id)
    destination_terminal = db.get(Terminal, destination.terminal_id)
    path = route(
        db, origin_terminal.node_id, destination_terminal.node_id, vessel, departure
    )
    elapsed, _ = (
        lock_wait(db, path["segments"], departure, 10) if path["passed"] else (None, [])
    )
    if (
        not path["passed"]
        or elapsed is None
        or departure + timedelta(hours=elapsed) > dt(destination.arrival)
    ):
        raise HTTPException(
            409, "Scheduled route or lock travel cannot fit stop times."
        )
    capability_failures = terminal_checks(
        db, cargo, vessel, origin_terminal
    ) + terminal_checks(db, cargo, vessel, destination_terminal)
    if capability_failures:
        raise HTTPException(
            409,
            {
                "message": "Scheduled terminals failed revalidation.",
                "reasons": capability_failures,
            },
        )
    reasons = compliance_checks(db, cargo, vessel, departure, eta)
    if reasons:
        raise HTTPException(
            409, {"message": "Scheduled voyage compliance failed.", "reasons": reasons}
        )
    return {
        **plan,
        "departure": departure.isoformat(),
        "loading_start": (departure - timedelta(hours=0.75)).isoformat(),
        "unloading_start": destination.arrival,
        "eta": eta.isoformat(),
        "hours": round((eta - dt(cargo.ready_time)).total_seconds() / 3600, 2),
    }


def propose_services(db):
    corridors = {}
    for cargo in db.scalars(select(CargoRequest)):
        key = (node_for(cargo.origin), node_for(cargo.destination))
        corridors.setdefault(key, []).append(cargo)
    proposals = [
        {
            "origin": key[0],
            "destination": key[1],
            "requested_tonnes": sum(c.weight_tonnes for c in cargos),
            "request_count": len(cargos),
            "proposed_capacity_tonnes": 150,
            "estimated_utilization_pct": round(
                min(1, sum(c.weight_tonnes for c in cargos) / 150) * 100, 1
            ),
            "proposal": "Mon / Wed / Fri pilot",
            "source": "Synthetic platform demand; exploratory aggregate, not forecasted frequency",
        }
        for key, cargos in corridors.items()
        if len(cargos) >= 2 and sum(c.weight_tonnes for c in cargos) >= 100
    ]
    for proposal in proposals:
        cargos = corridors[(proposal["origin"], proposal["destination"])]
        weeks = {dt(c.ready_time).isocalendar()[:2] for c in cargos}
        average = sum(c.weight_tonnes for c in cargos) / max(1, len(weeks))
        proposal.update(
            {
                "observed_weeks": len(weeks),
                "average_weekly_demand_tonnes": round(average, 1),
                "unserved_demand_tonnes": sum(
                    c.weight_tonnes
                    for c in cargos
                    if c.status in {"POSTED", "MATCHED", "QUOTED", "REPLANNING"}
                ),
                "recommended_departures_per_week": min(
                    7, max(1, __import__("math").ceil(average / 150))
                ),
                "forecast_status": "Insufficient recurring history"
                if len(weeks) < 2
                else "Descriptive demo-demand scenario",
                "source": "Calculated from synthetic platform demand by unique readiness weeks; exploratory service suggestion, not a validated forecast",
            }
        )
    return proposals
