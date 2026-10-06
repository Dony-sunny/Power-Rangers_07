from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.database import get_db
from backend.auth import get_actor, permission, cargo_access, vessel_access, ROLE_LABELS
from backend.models import *
from backend.repositories.common import uid, record, require, audit
from backend.schemas.requests import (
    CargoCreate,
    VesselCreate,
    AvailabilityCreate,
    BookingCreate,
    StateChange,
)
from backend.services.bookings import create_booking, transition, booking_access
from backend.services.planning import compare_modes
from feasibility.engine import check_feasibility
from optimization.matching.engine import match

router = APIRouter(prefix="/api")


@router.get("/workspace")
def get_workspace(db=Depends(get_db), actor=Depends(get_actor)):
    from backend.services.workspaces import workspace
    from backend.config import settings

    result = workspace(db, actor)
    result["demo_mode"] = settings.demo_mode
    return result


@router.get("/health")
def health():
    from backend.config import settings

    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "provider": settings.ai_provider,
        "operational_data": "SIMULATED",
        "roles": ROLE_LABELS,
    }


@router.post("/cargo", status_code=201)
def post_cargo(payload: CargoCreate, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "cargo_write")
    cargo = CargoRequest(
        id=uid("cargo"),
        organization_id=actor.organization_id,
        **payload.model_dump(mode="json"),
    )
    db.add(cargo)
    audit(db, "cargo.created", cargo.id, actor, weight_tonnes=cargo.weight_tonnes)
    db.commit()
    return record(cargo)


@router.post("/cargo/{cargo_id}/documents/{document_id}")
def link_document(
    cargo_id: str, document_id: str, db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "cargo_write")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    document = require(db, CargoDocument, document_id)
    if (
        document.organization_id != actor.organization_id
        or document.cargo_id
        and document.cargo_id != cargo_id
    ):
        raise HTTPException(404, "Document not found.")
    document.cargo_id = cargo_id
    db.commit()
    return {"linked": True}


@router.get("/cargo")
def list_cargo(db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "plan")
    from backend.auth import GLOBAL_ROLES

    query = select(CargoRequest).order_by(CargoRequest.created_at.desc())
    if actor.role_id not in GLOBAL_ROLES:
        query = query.where(CargoRequest.organization_id == actor.organization_id)
    return [record(item) for item in db.scalars(query)]


@router.post("/vessels", status_code=201)
def post_vessel(payload: VesselCreate, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "vessel_write")
    vessel = Vessel(
        id=uid("vessel"),
        organization_id=actor.organization_id,
        compliance_status="PENDING",
        reliability_score=0.5,
        **payload.model_dump(),
    )
    db.add(vessel)
    db.commit()
    return record(vessel)


@router.post("/availability", status_code=201)
def post_availability(
    payload: AvailabilityCreate, db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "availability_write")
    vessel = require(db, Vessel, payload.vessel_id)
    vessel_access(actor, vessel)
    if (
        payload.capacity_tonnes > vessel.max_capacity_tonnes
        or payload.volume_m3 > vessel.max_volume_m3
    ):
        raise HTTPException(422, "Listed availability cannot exceed vessel capacity.")
    availability = VesselAvailability(
        id=uid("availability"), **payload.model_dump(mode="json")
    )
    db.add(availability)
    audit(db, "vessel.available", vessel.id, actor)
    db.commit()
    opportunities = [
        c.id
        for c in db.scalars(select(CargoRequest))
        if c.status in {"POSTED", "MATCHED", "QUOTED"}
        and check_feasibility(db, c, vessel)["passed"]
    ]
    return {"availability": record(availability), "compatible_cargo_ids": opportunities}


@router.get("/cargo/{cargo_id}/matches")
def get_matches(
    cargo_id: str,
    profile: str = "BALANCED",
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    try:
        return match(db, cargo, profile, persist=True, actor=actor)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@router.get("/cargo/{cargo_id}/compare")
def comparison(
    cargo_id: str,
    vessel_id: str | None = None,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    from backend.services.demo_state import flood_enabled

    return compare_modes(db, cargo, vessel_id, flood=flood_enabled(db))


@router.post("/bookings", status_code=201)
def post_booking(payload: BookingCreate, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "book")
    return create_booking(db, actor, payload)


@router.post("/shipments/{shipment_id}/transition")
def change_state(
    shipment_id: str, payload: StateChange, db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "execute")
    from backend.services.bookings import lock_writes

    lock_writes(db)
    return transition(db, actor, require(db, Shipment, shipment_id), payload.status)


@router.get("/shipments/{shipment_id}")
def tracking(shipment_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    shipment = require(db, Shipment, shipment_id)
    booking = require(db, Booking, shipment.booking_id)
    booking_access(db, actor, booking)
    return {
        "shipment": record(shipment),
        "events": [
            record(e)
            for e in db.scalars(
                select(TrackingEvent)
                .where(TrackingEvent.shipment_id == shipment_id)
                .order_by(TrackingEvent.timestamp)
            )
        ],
        "legs": [
            record(e)
            for e in db.scalars(
                select(ShipmentLeg)
                .where(ShipmentLeg.shipment_id == shipment_id)
                .order_by(ShipmentLeg.sequence)
            )
        ],
        "eta": booking.eta,
        "simulated": True,
    }
