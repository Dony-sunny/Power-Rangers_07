from datetime import date, datetime, timedelta, time
from sqlalchemy import select
from fastapi import HTTPException
from backend.models import *
from backend.repositories.common import uid, require, record, audit
from backend.services.timeutils import dt, IST
from backend.auth import vessel_access, cargo_access
from optimization.scheduled_services.planner import segment_usage


def segment_limit(db, service, sequence):
    occurrence = db.scalar(
        select(ServiceOccurrence).where(ServiceOccurrence.service_id == service.id)
    )
    pattern = db.get(ServicePattern, occurrence.pattern_id) if occurrence else None
    return (
        min(
            service.capacity_tonnes,
            pattern.segment_capacities.get(str(sequence), service.capacity_tonnes),
        )
        if pattern
        else service.capacity_tonnes
    )


def generate_pattern(db, actor, payload):
    from backend.services.bookings import lock_writes

    lock_writes(db)
    template = require(db, ScheduledService, payload.template_service_id)
    vessel = require(db, Vessel, template.vessel_id)
    if actor.role_id not in {"admin", "control"}:
        vessel_access(actor, vessel)
    if payload.capacity_tonnes > vessel.max_capacity_tonnes:
        raise HTTPException(422, "Service capacity exceeds vessel capacity.")
    stops = list(
        db.scalars(
            select(ScheduledServiceStop)
            .where(ScheduledServiceStop.service_id == template.id)
            .order_by(ScheduledServiceStop.sequence)
        )
    )
    if len(stops) < 2:
        raise HTTPException(422, "A service needs at least two stops.")
    anchor = dt(stops[0].departure)
    definitions = [
        {
            "terminal_id": stop.terminal_id,
            "sequence": stop.sequence,
            "arrival_minutes": (dt(stop.arrival) - anchor).total_seconds() / 60,
            "departure_minutes": (dt(stop.departure) - anchor).total_seconds() / 60,
        }
        for stop in stops
    ]
    if set(payload.segment_capacities) - {str(stop.sequence) for stop in stops[:-1]}:
        raise HTTPException(
            422, "Segment capacity keys must identify a template stop-to-stop segment."
        )
    limits = {
        str(stop.sequence): payload.segment_capacities.get(
            str(stop.sequence), payload.capacity_tonnes
        )
        for stop in stops[:-1]
    }
    if any(value <= 0 or value > payload.capacity_tonnes for value in limits.values()):
        raise HTTPException(
            422, "Segment limits must be positive and within service capacity."
        )
    pattern = ServicePattern(
        id=uid("pattern"),
        name=payload.name,
        vessel_id=vessel.id,
        operating_days=payload.operating_days,
        departure_time=payload.departure_time,
        effective_date=payload.effective_date.isoformat(),
        end_date=payload.end_date.isoformat(),
        capacity_tonnes=payload.capacity_tonnes,
        segment_capacities=limits,
        stops=definitions,
        vessel_class=vessel.vessel_type,
    )
    db.add(pattern)
    db.flush()
    day = payload.effective_date
    created = []
    while day <= payload.end_date:
        if day.weekday() in payload.operating_days:
            departure = datetime.combine(
                day, time.fromisoformat(payload.departure_time), tzinfo=IST
            )
            service = ScheduledService(
                id=uid("service"),
                name=payload.name,
                vessel_id=vessel.id,
                departure=departure.isoformat(),
                capacity_tonnes=payload.capacity_tonnes,
                recurrence=" / ".join(
                    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]
                    for i in payload.operating_days
                ),
            )
            db.add(service)
            db.flush()
            for definition in definitions:
                db.add(
                    ScheduledServiceStop(
                        id=uid("stop"),
                        service_id=service.id,
                        terminal_id=definition["terminal_id"],
                        sequence=definition["sequence"],
                        arrival=(
                            departure + timedelta(minutes=definition["arrival_minutes"])
                        ).isoformat(),
                        departure=(
                            departure
                            + timedelta(minutes=definition["departure_minutes"])
                        ).isoformat(),
                    )
                )
            db.add(
                ServiceOccurrence(
                    id=uid("occurrence"),
                    pattern_id=pattern.id,
                    service_id=service.id,
                    operating_date=day.isoformat(),
                )
            )
            origin = db.get(
                WaterwayNode, db.get(Terminal, definitions[0]["terminal_id"]).node_id
            ).name
            destination = db.get(
                WaterwayNode, db.get(Terminal, definitions[-1]["terminal_id"]).node_id
            ).name
            db.add(
                VesselAvailability(
                    id=uid("availability"),
                    vessel_id=vessel.id,
                    origin=origin,
                    destination=destination,
                    available_from=(departure - timedelta(hours=2)).isoformat(),
                    available_until=(
                        departure
                        + timedelta(minutes=definitions[-1]["arrival_minutes"], hours=4)
                    ).isoformat(),
                    capacity_tonnes=payload.capacity_tonnes,
                    volume_m3=vessel.max_volume_m3,
                )
            )
            created.append(service.id)
        day += timedelta(days=1)
    audit(db, "service.pattern_created", pattern.id, actor, departures=len(created))
    db.commit()
    return {
        "pattern": record(pattern),
        "service_ids": created,
        "source": "Dated departures generated from configured demo schedule, not a live carrier timetable",
    }


def held_capacity(db, service_id, sequence, exclude_contract=None):
    held = 0
    for reservation in db.scalars(
        select(ContractReservation).where(ContractReservation.service_id == service_id)
    ):
        contract = db.get(CapacityContract, reservation.contract_id)
        if (
            contract.status != "ACTIVE"
            or contract.id == exclude_contract
            or not contract.start_sequence <= sequence < contract.end_sequence
        ):
            continue
        drawn = sum(
            draw.tonnes
            for draw in db.scalars(
                select(ContractDraw).where(
                    ContractDraw.contract_id == contract.id,
                    ContractDraw.service_id == service_id,
                )
            )
            if db.get(Booking, draw.booking_id).status not in {"CANCELLED", "FAILED"}
        )
        held += max(0, reservation.tonnes - drawn)
    return held


def create_contract(db, actor, payload):
    from backend.services.bookings import lock_writes

    lock_writes(db)
    pattern = require(db, ServicePattern, payload.pattern_id)
    if payload.start_date < date.fromisoformat(
        pattern.effective_date
    ) or payload.end_date > date.fromisoformat(pattern.end_date):
        raise HTTPException(422, "Contract dates must fit generated service dates.")
    occurrences = list(
        db.scalars(
            select(ServiceOccurrence).where(ServiceOccurrence.pattern_id == pattern.id)
        )
    )
    selected = [
        item
        for item in occurrences
        if payload.start_date.isoformat()
        <= item.operating_date
        <= payload.end_date.isoformat()
        and item.status == "SCHEDULED"
    ]
    if (
        not selected
        or payload.start_sequence < 0
        or payload.end_sequence >= len(pattern.stops)
        or payload.start_sequence >= payload.end_sequence
    ):
        raise HTTPException(
            422, "Contract needs scheduled departures and a valid stop pair."
        )
    contract = CapacityContract(
        id=uid("contract"),
        organization_id=actor.organization_id,
        **payload.model_dump(mode="json"),
    )
    for occurrence in selected:
        service = db.get(ScheduledService, occurrence.service_id)
        usage = segment_usage(db, service)
        if any(
            usage[seq] + payload.tonnes_per_departure > segment_limit(db, service, seq)
            for seq in usage
            if payload.start_sequence <= seq < payload.end_sequence
        ):
            raise HTTPException(
                409, "Contract capacity exceeds an available service segment."
            )
    weekly = payload.tonnes_per_departure * len(pattern.operating_days)
    if (
        payload.weekly_commitment_tonnes > weekly
        or payload.minimum_commitment_tonnes
        > payload.tonnes_per_departure * len(selected)
    ):
        raise HTTPException(422, "Commitment exceeds the reserved departures.")
    db.add(contract)
    db.flush()
    for occurrence in selected:
        db.add(
            ContractReservation(
                id=uid("contract-capacity"),
                contract_id=contract.id,
                service_id=occurrence.service_id,
                tonnes=payload.tonnes_per_departure,
            )
        )
    audit(
        db, "contract.capacity_reserved", contract.id, actor, departures=len(selected)
    )
    db.commit()
    return {
        "contract": record(contract),
        "reserved_departures": len(selected),
        "legal_status": "Prototype commercial record; not a legal contract",
    }


def recurring_bookings(db, actor, payload):
    from backend.services.bookings import create_booking, lock_writes
    from backend.schemas.requests import BookingCreate

    lock_writes(db)
    if not payload.approved:
        raise HTTPException(422, "Approve recurring bookings explicitly.")
    anchor = require(db, CargoRequest, payload.cargo_id)
    cargo_access(actor, anchor)
    results = []
    for index, service_id in enumerate(payload.service_ids):
        service = require(db, ScheduledService, service_id)
        offset = dt(service.departure).date() - dt(anchor.ready_time).date()
        cargo = anchor
        if index or offset.days:
            fields = record(anchor)
            for key in ["id", "status", "created_at"]:
                fields.pop(key, None)
            fields["ready_time"] = (dt(anchor.ready_time) + offset).isoformat()
            fields["delivery_deadline"] = (
                dt(anchor.delivery_deadline) + offset
            ).isoformat()
            cargo = CargoRequest(id=uid("recurring-cargo"), **fields)
            db.add(cargo)
            db.flush()
        request = BookingCreate(
            cargo_id=cargo.id,
            vessel_id=service.vessel_id,
            service_id=service.id,
            contract_id=payload.contract_id,
            mode="HYBRID"
            if cargo.first_mile_required or cargo.last_mile_required
            else "WATER",
            approved=True,
        )
        results.append(
            create_booking(db, actor, request, commit=False, acquire_lock=False)
        )
    audit(db, "service.recurring_booked", anchor.id, actor, count=len(results))
    db.commit()
    return {
        "results": results,
        "booking_count": len(results),
        "source": "Explicitly approved separate cargo occurrences; atomic all-or-none reservation",
    }
