from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.database import get_db
from backend.auth import get_actor, permission, cargo_access, vessel_access, ROLE_LABELS
from backend.models import *
from backend.repositories.common import uid, record, require, audit
from backend.schemas.requests import (
    CargoCreate,
    VesselCreate,
    VesselListing,
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
    if actor.role_id == "control":
        from backend.auth import coordinated_orgs
        query = query.where(CargoRequest.organization_id.in_(coordinated_orgs(db, actor)))
    elif actor.role_id not in GLOBAL_ROLES:
        query = query.where(CargoRequest.organization_id == actor.organization_id)
    return [record(item) for item in db.scalars(query)]


@router.post("/vessels/with-availability", status_code=201)
def register_boat_listing(payload: VesselListing, db=Depends(get_db), actor=Depends(get_actor)):
    from datetime import timedelta
    from backend.config import settings
    from backend.services.bookings import lock_writes
    from backend.services.timeutils import utcnow
    permission(actor, "vessel_write")
    permission(actor, "availability_write")
    if payload.demo_certificate_review and not settings.demo_mode:
        raise HTTPException(403, "Simulated certificate review is only available in demo mode.")
    if payload.availability.capacity_tonnes > payload.vessel.max_capacity_tonnes or payload.availability.volume_m3 > payload.vessel.max_volume_m3:
        raise HTTPException(422, "Listed availability cannot exceed the boat’s physical capacity.")
    lock_writes(db)
    vessel = Vessel(id=uid("vessel"), organization_id=actor.organization_id,
                    compliance_status="PASS" if payload.demo_certificate_review else "PENDING",
                    reliability_score=0.5, **payload.vessel.model_dump())
    db.add(vessel)
    db.flush()
    availability = VesselAvailability(id=uid("availability"), vessel_id=vessel.id,
                                      **payload.availability.model_dump(mode="json"))
    db.add(availability)
    if payload.demo_certificate_review:
        expires = max(utcnow(), payload.availability.available_until) + timedelta(days=365)
        for kind in ["REGISTRATION", "INSURANCE"]:
            db.add(VesselCertificate(id=uid("certificate"), vessel_id=vessel.id, kind=kind,
                                     expires_at=expires.isoformat(), verified=True))
        vessel.trust_metrics = {"certificate_source": "SIMULATED demo review; no real documents verified"}
    audit(db, "vessel.registered_with_availability", vessel.id, actor,
          certificate_source="SIMULATED" if payload.demo_certificate_review else "PENDING_REVIEW")
    db.commit()
    return {"vessel": record(vessel), "availability": record(availability),
            "certificate_source": "SIMULATED" if payload.demo_certificate_review else "PENDING_REVIEW"}


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


def editable_availability(db, actor, availability_id):
    from backend.services.bookings import lock_writes
    from backend.services.cargo_lines import expire
    from feasibility.vessel_constraints.checks import ACTIVE_BOOKING_STATES

    permission(actor, "availability_write")
    lock_writes(db)
    listing = require(db, VesselAvailability, availability_id)
    vessel_access(actor, require(db, Vessel, listing.vessel_id))
    expire(db)
    for voyage in db.scalars(select(CargoVoyage).where(CargoVoyage.status.in_(["HELD", "CONFIRMED"]))):
        if voyage.plan["availability_id"] == availability_id:
            raise HTTPException(409, "This listing is reserved by a departure. Publish a new availability window instead.")
    if db.scalar(select(Booking).where(Booking.availability_id == availability_id, Booking.status.in_(ACTIVE_BOOKING_STATES))):
        raise HTTPException(409, "This listing is reserved by a booking. Publish a new availability window instead.")
    return listing


@router.put("/availability/{availability_id}")
def update_availability(availability_id: str, payload: AvailabilityCreate, db=Depends(get_db), actor=Depends(get_actor)):
    listing = editable_availability(db, actor, availability_id)
    if payload.vessel_id != listing.vessel_id:
        raise HTTPException(422, "An availability listing must stay with its registered boat.")
    vessel = require(db, Vessel, listing.vessel_id)
    if payload.capacity_tonnes > vessel.max_capacity_tonnes or payload.volume_m3 > vessel.max_volume_m3:
        raise HTTPException(422, "Listed availability cannot exceed vessel capacity.")
    for key, value in payload.model_dump(mode="json").items():
        setattr(listing, key, value)
    audit(db, "vessel.availability_updated", listing.id, actor)
    db.commit()
    return record(listing)


@router.post("/availability/{availability_id}/visibility")
def availability_visibility(availability_id: str, active: bool, db=Depends(get_db), actor=Depends(get_actor)):
    listing = editable_availability(db, actor, availability_id)
    listing.active = active
    audit(db, "vessel.availability_visibility", listing.id, actor, active=active)
    db.commit()
    return record(listing)


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
