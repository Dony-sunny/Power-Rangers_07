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


def segment_usage(db, service):
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
    return used


def validate_capacity(db, service, cargo):
    origin, destination = stop_pair(db, service, cargo)
    if any(
        used + cargo.weight_tonnes > service.capacity_tonnes + 1e-9
        for seq, used in segment_usage(db, service).items()
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
    return [
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
