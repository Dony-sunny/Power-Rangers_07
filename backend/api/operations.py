from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.database import get_db
from backend.auth import get_actor, permission, vessel_access, GLOBAL_ROLES
from backend.models import *
from backend.schemas.requests import (
    Disruption,
    RecoveryApproval,
    OperationUpdate,
    NavigationCreate,
    MaintenanceUpdate,
    PaymentUpdate,
    StrictModel,
)
from backend.repositories.common import require, record, uid, audit
from backend.services.bookings import booking_access
from backend.services.timeutils import utcnow, dt
from backend.services.recovery import disrupt, alternatives, approve_recovery
from backend.services.recovery import approve_pool_recovery
from backend.services.impact import calculate_impact, modal_shift
from backend.services.documents import generate_document
from pydantic import Field

router = APIRouter(prefix="/api", tags=["operations"])


@router.get("/impact")
def impact(db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "metrics")
    return calculate_impact(db)


@router.get("/intelligence/modal-shift")
def intelligence(db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "metrics")
    return modal_shift(db)


@router.post("/bookings/{booking_id}/disrupt")
def disruption(
    booking_id: str, payload: Disruption, db=Depends(get_db), actor=Depends(get_actor)
):
    from backend.config import settings

    permission(actor, "recover")
    if not settings.demo_mode:
        raise HTTPException(403, "Synthetic disruption controls are demo-only.")
    return disrupt(
        db, actor, require(db, Booking, booking_id), payload.kind, payload.model_dump()
    )


@router.get("/bookings/{booking_id}/recovery")
def recovery(booking_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "recover")
    booking = require(db, Booking, booking_id)
    booking_access(db, actor, booking)
    return alternatives(db, booking, actor)


@router.post("/bookings/{booking_id}/recover")
def recover(
    booking_id: str,
    payload: RecoveryApproval,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "recover")
    return approve_recovery(db, actor, require(db, Booking, booking_id), payload)


@router.get("/bookings/{booking_id}/documents/{kind}")
def document(booking_id: str, kind: str, db=Depends(get_db), actor=Depends(get_actor)):
    return generate_document(db, actor, require(db, Booking, booking_id), kind)


@router.post("/bookings/{booking_id}/recover-pool")
def recover_pool(
    booking_id: str,
    payload: RecoveryApproval,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "recover")
    return approve_pool_recovery(db, actor, require(db, Booking, booking_id), payload)


@router.post("/shipments/{shipment_id}/operations")
def operations(
    shipment_id: str,
    payload: OperationUpdate,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    allowed = {
        "warehouse",
        "receiver",
        "dispatch",
        "terminal",
        "fleet",
        "control",
        "admin",
    }
    if actor.role_id not in allowed:
        raise HTTPException(403, "Role cannot update cargo handover records.")
    shipment = require(db, Shipment, shipment_id)
    booking = require(db, Booking, shipment.booking_id)
    booking_access(db, actor, booking)
    updates = payload.model_dump(exclude_none=True)
    warehouse_keys = {
        "actual_weight_tonnes",
        "actual_volume_m3",
        "packing_ready",
        "handover_confirmed",
        "gate_out",
        "loading_sequence",
    }
    receiver_keys = {"quantity_received_tonnes", "damage_report", "delivery_signature"}
    if (
        actor.role_id == "warehouse"
        and not set(updates) <= warehouse_keys
        or actor.role_id == "receiver"
        and not set(updates) <= receiver_keys
        or actor.role_id == "fleet"
        and not set(updates) <= {"crew_assignment"}
    ):
        raise HTTPException(403, "These fields belong to another operational role.")
    cargo = db.get(CargoRequest, booking.cargo_id)
    if (
        payload.actual_weight_tonnes
        and abs(payload.actual_weight_tonnes - cargo.weight_tonnes) > 0.01
    ):
        raise HTTPException(
            409,
            "Actual weight differs from booked weight. Replan and revalidate capacity before loading.",
        )
    if payload.actual_volume_m3:
        if shipment.status not in {"CONFIRMED", "SCHEDULED", "LOADING"}:
            raise HTTPException(409, "Volume verification must occur before departure.")
        if booking.vessel_id:
            vessel = db.get(Vessel, booking.vessel_id)
            from feasibility.vessel_constraints.checks import reserved

            _, occupied_volume, _ = reserved(
                db, vessel.id, booking.departure, booking.eta, [booking.id]
            )
            availability = db.get(VesselAvailability, booking.availability_id)
            limit = (
                min(vessel.max_volume_m3, availability.volume_m3)
                if availability
                else vessel.max_volume_m3
            )
            if occupied_volume + payload.actual_volume_m3 > limit:
                raise HTTPException(
                    409, "Verified cargo volume exceeds remaining voyage volume."
                )
        cargo.volume_m3 = payload.actual_volume_m3
    shipment.operational_data = {
        **shipment.operational_data,
        **updates,
        "updated_at": utcnow().isoformat(),
    }
    audit(db, "shipment.handover_updated", shipment.id, actor, fields=list(updates))
    db.commit()
    return record(shipment)


@router.post("/reports", status_code=201)
def report(payload: NavigationCreate, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "report")
    require(db, WaterwaySegment, payload.segment_id)
    if (
        not -90 <= payload.coordinates[0] <= 90
        or not -180 <= payload.coordinates[1] <= 180
    ):
        raise HTTPException(422, "Invalid report coordinates.")
    report = NavigationReport(
        id=uid("report"),
        reporter_id=actor.id,
        expires_at=(utcnow() + timedelta(hours=24)).isoformat(),
        **payload.model_dump(mode="json"),
    )
    db.add(report)
    audit(db, "navigation.reported", report.id, actor, verification_status="UNVERIFIED")
    db.commit()
    return record(report)


@router.post("/vessels/{vessel_id}/maintenance")
def maintenance(
    vessel_id: str,
    payload: MaintenanceUpdate,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "maintain")
    vessel = require(db, Vessel, vessel_id)
    vessel_access(actor, vessel)
    if payload.status == "OPERATIONAL" and any(
        b.status in {"LOADING", "IN_TRANSIT", "UNLOADING"}
        for b in db.scalars(select(Booking).where(Booking.vessel_id == vessel_id))
    ):
        raise HTTPException(
            409, "Cannot return a vessel to service during an active voyage."
        )
    vessel.maintenance_status = payload.status
    vessel.state = "AVAILABLE" if payload.status == "OPERATIONAL" else "MAINTENANCE"
    maintenance = db.scalar(
        select(VesselMaintenanceStatus).where(
            VesselMaintenanceStatus.vessel_id == vessel_id
        )
    )
    if not maintenance:
        maintenance = VesselMaintenanceStatus(
            id=uid("maintenance"), vessel_id=vessel_id, status=payload.status
        )
        db.add(maintenance)
    maintenance.status = payload.status
    maintenance.defect = payload.defect
    if payload.status == "OPERATIONAL":
        maintenance.inspection_date = utcnow().date().isoformat()
        maintenance.due_date = (utcnow() + timedelta(days=30)).date().isoformat()
        maintenance.return_to_service = utcnow().isoformat()
    audit(db, "vessel.maintenance_updated", vessel_id, actor, status=payload.status)
    db.commit()
    return record(vessel)


class CertificateCreate(StrictModel):
    kind: str = Field(pattern="^(REGISTRATION|INSURANCE|DANGEROUS_GOODS)$")
    expires_at: str
    verified: bool = False


@router.post("/vessels/{vessel_id}/certificates")
def certificate(
    vessel_id: str,
    payload: CertificateCreate,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    if actor.role_id not in {"compliance", "admin"}:
        raise HTTPException(403, "Certificate review requires a compliance role.")
    vessel = require(db, Vessel, vessel_id)
    try:
        expiry = dt(payload.expires_at)
        if (
            expiry <= utcnow()
            or __import__("datetime").datetime.fromisoformat(payload.expires_at).tzinfo
            is None
        ):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(
            422, "Certificate requires a future timezone-aware expiry."
        ) from None
    item = VesselCertificate(
        id=uid("certificate"), vessel_id=vessel_id, **payload.model_dump()
    )
    db.add(item)
    db.flush()
    certificates = list(
        db.scalars(
            select(VesselCertificate).where(VesselCertificate.vessel_id == vessel_id)
        )
    )
    vessel.compliance_status = (
        "PASS"
        if all(
            any(
                c.kind == kind and c.verified and dt(c.expires_at) > utcnow()
                for c in certificates
            )
            for kind in ["REGISTRATION", "INSURANCE"]
        )
        else "PENDING"
    )
    audit(
        db,
        "compliance.certificate_reviewed",
        item.id,
        actor,
        kind=payload.kind,
        verified=payload.verified,
    )
    db.commit()
    return record(item)


@router.post("/payments/{payment_id}/status")
def payment(
    payment_id: str,
    payload: PaymentUpdate,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "finance")
    payment = require(db, PaymentRecord, payment_id)
    invoice = require(db, InvoiceRecord, payment.invoice_id)
    booking = require(db, Booking, invoice.booking_id)
    booking_access(db, actor, booking)
    transitions = {
        "PENDING": {"PAID", "DISPUTED"},
        "PAID": {"SETTLED", "DISPUTED"},
        "DISPUTED": {"PENDING"},
        "SETTLED": set(),
    }
    if payload.status not in transitions[payment.status]:
        raise HTTPException(409, "Invalid payment-state transition.")
    if payload.status == "SETTLED" and booking.status != "DELIVERED":
        raise HTTPException(409, "Complete delivery before operator settlement.")
    payment.status = payload.status
    payment.dispute = payload.dispute
    invoice.status = (
        "PAID"
        if payload.status in {"PAID", "SETTLED"}
        else "DISPUTED"
        if payload.status == "DISPUTED"
        else "DRAFT"
    )
    audit(db, "payment.status_changed", payment.id, actor, status=payload.status)
    db.commit()
    return record(payment)


@router.get("/payments/{payment_id}/history")
def payment_history(payment_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "finance")
    item = require(db, PaymentRecord, payment_id)
    invoice = require(db, InvoiceRecord, item.invoice_id)
    booking_access(db, actor, require(db, Booking, invoice.booking_id))
    return {
        "events": [
            record(event)
            for event in db.scalars(
                select(AuditEvent)
                .where(AuditEvent.entity_id == item.id)
                .order_by(AuditEvent.timestamp)
            )
        ]
    }
