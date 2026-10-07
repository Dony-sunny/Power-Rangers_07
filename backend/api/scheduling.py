from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.database import get_db
from backend.auth import get_actor, permission, GLOBAL_ROLES, coordinated_orgs
from backend.models import *
from backend.schemas.extensions import (
    PatternCreate,
    RecurringBooking,
    ContractCreate,
    ResourceCreate,
    ReservationCreate,
    TruckCreate,
)
from backend.repositories.common import require, uid, record, audit
from backend.services.recurring import (
    generate_pattern,
    recurring_bookings,
    create_contract,
)
from backend.services.bookings import lock_writes, booking_access
from backend.services.terminal_resources import calendar, reservations, peak_quantity
from backend.services.timeutils import dt

router = APIRouter(prefix="/api", tags=["recurring services and terminal resources"])


@router.post("/service-patterns", status_code=201)
def pattern(payload: PatternCreate, db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id not in {"operator", "fleet", "control", "admin"}:
        raise HTTPException(
            403, "Service planning requires fleet or control permissions."
        )
    return generate_pattern(db, actor, payload)


@router.get("/service-patterns")
def patterns(db=Depends(get_db), actor=Depends(get_actor)):
    return {
        "patterns": [record(item) for item in db.scalars(select(ServicePattern))],
        "occurrences": [record(item) for item in db.scalars(select(ServiceOccurrence))],
        "contracts": [
            record(item)
            for item in db.scalars(select(CapacityContract))
            if actor.role_id == "admin"
            or actor.role_id == "control" and item.organization_id in coordinated_orgs(db, actor)
            or item.organization_id == actor.organization_id
        ],
    }


@router.post("/services/recurring-bookings", status_code=201)
def repeat(payload: RecurringBooking, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "book")
    return recurring_bookings(db, actor, payload)


@router.post("/services/{service_id}/cancel")
def cancel(service_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id not in {"admin", "control", "fleet", "operator"}:
        raise HTTPException(403, "Service cancellation requires dispatch permissions.")
    lock_writes(db)
    service = require(db, ScheduledService, service_id)
    if (
        actor.role_id not in {"admin", "control"}
        and db.get(Vessel, service.vessel_id).organization_id != actor.organization_id
    ):
        raise HTTPException(404, "Service not found.")
    service.active = False
    occurrence = db.scalar(
        select(ServiceOccurrence).where(ServiceOccurrence.service_id == service_id)
    )
    if occurrence:
        occurrence.status = "CANCELLED"
    affected = []
    for capacity in db.scalars(
        select(ScheduledCapacityBooking).where(
            ScheduledCapacityBooking.service_id == service_id
        )
    ):
        booking = db.get(Booking, capacity.booking_id)
        if booking.status in {"CONFIRMED", "SCHEDULED"}:
            booking.status = "REPLANNING"
            shipment = db.scalar(
                select(Shipment).where(Shipment.booking_id == booking.id)
            )
            shipment.status = "REPLANNING"
            db.get(CargoRequest, booking.cargo_id).status = "REPLANNING"
            affected.append(booking.id)
    audit(
        db,
        "service.occurrence_cancelled",
        service_id,
        actor,
        affected_bookings=affected,
    )
    db.commit()
    return {
        "cancelled_service": service_id,
        "affected_bookings": affected,
        "pattern_preserved": True,
    }


@router.post("/capacity-contracts", status_code=201)
def contract(payload: ContractCreate, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "book")
    return create_contract(db, actor, payload)


def terminal_access(db, actor, terminal_id):
    terminal = require(db, Terminal, terminal_id)
    if (
        actor.role_id not in {"admin", "control", "terminal"}
        or actor.role_id == "terminal"
        and terminal.organization_id != actor.organization_id
    ):
        raise HTTPException(404, "Terminal not found.")
    return terminal


@router.get("/terminals/resources")
def resources(db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id not in {"terminal", "control", "fleet", "dispatch", "admin"}:
        raise HTTPException(403, "Terminal calendar requires operations access.")
    terminals = [
        item.id
        for item in db.scalars(select(Terminal))
        if actor.role_id in {"admin", "control", "dispatch", "fleet"}
        or item.organization_id == actor.organization_id
    ]
    result = calendar(db, terminals)
    result["truck_appointments"] = [
        record(item)
        for item in db.scalars(select(TruckAppointment))
        if item.terminal_id in terminals
    ]
    if actor.role_id in {"dispatch", "fleet"}:
        # Shared calendar exposes occupied windows, not competitor shipment/provider data.
        for item in result["reservations"] + result["queue"]:
            item.pop("booking_id", None)
            item.pop("description", None)
        result["truck_appointments"] = [
            item
            for item in result["truck_appointments"]
            if actor.role_id == "dispatch"
            and db.get(
                CargoRequest,
                db.get(
                    Booking, db.get(Shipment, item["shipment_id"]).booking_id
                ).cargo_id,
            ).organization_id
            == actor.organization_id
        ]
    if actor.role_id in {"control", "dispatch", "fleet"}:
        visible = set()
        for booking in db.scalars(select(Booking)):
            try:
                booking_access(db, actor, booking)
                visible.add(booking.id)
            except HTTPException:
                pass
        for row in result["reservations"] + result["queue"]:
            permitted = row.get("booking_id") in visible
            if row.get("voyage_id"):
                voyage = db.get(CargoVoyage, row["voyage_id"])
                permitted = actor.role_id == "control" and voyage.coordinator_org_id == actor.organization_id
            if not permitted:
                for key in ["booking_id", "description", "cargo_id", "voyage_id", "provider_org_id", "provider_reference", "truck_resource_id"]:
                    row.pop(key, None)
        result["truck_appointments"] = [row for row in result["truck_appointments"] if db.get(Shipment, row["shipment_id"]).booking_id in visible]
    return result


@router.post("/terminals/resources", status_code=201)
def resource(payload: ResourceCreate, db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id == "control":
        raise HTTPException(403, "Only terminal owners/admin maintain resource catalogs; coordinators allocate entrusted jobs.")
    terminal_access(db, actor, payload.terminal_id)
    item = TerminalResource(id=uid("resource"), **payload.model_dump())
    db.add(item)
    audit(db, "terminal.resource_created", item.id, actor)
    db.commit()
    return record(item)


@router.post("/terminals/reservations", status_code=201)
def reserve(payload: ReservationCreate, db=Depends(get_db), actor=Depends(get_actor)):
    lock_writes(db)
    resource = require(db, TerminalResource, payload.resource_id)
    terminal_access(db, actor, resource.terminal_id)
    if actor.role_id == "control":
        if not payload.booking_id:
            raise HTTPException(403, "Coordinator reservation must belong to an entrusted booking.")
        booking = require(db, Booking, payload.booking_id)
        booking_access(db, actor, booking)
        if resource.terminal_id not in {booking.origin_terminal_id, booking.destination_terminal_id}:
            raise HTTPException(403, "Resource does not belong to the entrusted shipment's terminals.")
    existing = reservations(db, resource, ())
    if (
        not resource.active
        or peak_quantity(existing, payload.starts_at, payload.ends_at)
        + payload.quantity
        > resource.capacity
    ):
        ends = [
            dt(item.ends_at)
            for item in existing
            if dt(item.ends_at) > payload.starts_at
        ]
        raise HTTPException(
            409,
            {
                "message": "Resource slot collision.",
                "reasons": [
                    f"Suggested next start: {min(ends).isoformat() if ends else 'resource unavailable'}"
                ],
            },
        )
    item = ResourceReservation(
        id=uid("resource-reservation"), **payload.model_dump(mode="json")
    )
    db.add(item)
    audit(db, "terminal.resource_reserved", item.id, actor)
    db.commit()
    return record(item)


@router.post("/terminals/truck-appointments", status_code=201)
def appointment(payload: TruckCreate, db=Depends(get_db), actor=Depends(get_actor)):
    lock_writes(db)
    shipment = require(db, Shipment, payload.shipment_id)
    booking = require(db, Booking, shipment.booking_id)
    booking_access(db, actor, booking)
    if actor.role_id not in {
        "terminal",
        "dispatch",
        "control",
        "admin",
    } or payload.terminal_id not in {
        booking.origin_terminal_id,
        booking.destination_terminal_id,
    }:
        raise HTTPException(
            403, "Appointment must belong to an assigned shipment terminal."
        )
    gate = db.scalar(
        select(TerminalResource).where(
            TerminalResource.terminal_id == payload.terminal_id,
            TerminalResource.kind == "TRUCK_GATE",
            TerminalResource.active == True,
        )
    )
    if (
        not gate
        or peak_quantity(reservations(db, gate, ()), payload.starts_at, payload.ends_at)
        + 1
        > gate.capacity
    ):
        raise HTTPException(409, "Truck gate is unavailable at the requested time.")
    item = TruckAppointment(id=uid("truck"), **payload.model_dump(mode="json"))
    db.add(item)
    db.add(
        ResourceReservation(
            id=uid("gate-slot"),
            resource_id=gate.id,
            booking_id=booking.id,
            starts_at=payload.starts_at.isoformat(),
            ends_at=payload.ends_at.isoformat(),
            quantity=1,
            description=payload.carrier,
        )
    )
    shipment.operational_data = {
        **shipment.operational_data,
        "truck_assignment": payload.carrier,
    }
    audit(db, "terminal.truck_appointed", item.id, actor)
    db.commit()
    return record(item)
