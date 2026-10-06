from backend.models import CargoRequest, Vessel
from backend.repositories.common import record
from backend.services.bookings import booking_access
from backend.auth import COMMERCIAL_ROLES
from fastapi import HTTPException

DOCUMENT_KINDS = {
    "confirmation",
    "manifest",
    "loading-sheet",
    "transport-instruction",
    "delivery-note",
    "invoice",
    "proof-of-delivery",
}


def generate_document(db, actor, booking, kind):
    booking_access(db, actor, booking)
    if kind not in DOCUMENT_KINDS:
        raise HTTPException(404, "Document type not found.")
    if kind in {"invoice", "confirmation"} and actor.role_id not in COMMERCIAL_ROLES:
        raise HTTPException(403, "Commercial document access is restricted.")
    cargo = db.get(CargoRequest, booking.cargo_id)
    vessel = db.get(Vessel, booking.vessel_id) if booking.vessel_id else None
    details = {
        "title": f"Jalayatra {kind.replace('-', ' ').title()}",
        "reference": booking.id,
        "status": booking.status,
        "cargo": {
            "type": cargo.cargo_type,
            "weight_tonnes": cargo.weight_tonnes,
            "volume_m3": cargo.volume_m3,
            "packaging": cargo.packaging,
            "hazardous": cargo.hazardous,
        },
        "origin": cargo.origin,
        "destination": cargo.destination,
        "vessel": vessel.name if vessel else "Road carrier",
        "departure": booking.departure,
        "eta": booking.eta,
        "notice": "PROTOTYPE DOCUMENT. Not an official e-way bill, statutory manifest or tax invoice. Operational data is simulated.",
    }
    if kind in {"confirmation", "invoice"}:
        details["total_inr"] = booking.total_cost
        details["charges"] = booking.cost_breakdown
    if booking.pool_id and kind in {
        "manifest",
        "loading-sheet",
        "transport-instruction",
    }:
        from sqlalchemy import select
        from backend.models import Booking

        loads = []
        for member in db.scalars(
            select(Booking).where(
                Booking.pool_id == booking.pool_id,
                Booking.status.not_in(["CANCELLED", "FAILED"]),
            )
        ):
            load = db.get(CargoRequest, member.cargo_id)
            loads.append(
                {
                    "cargo_reference": load.id,
                    "cargo_type": load.cargo_type,
                    "weight_tonnes": load.weight_tonnes,
                    "volume_m3": load.volume_m3,
                    "packaging": load.packaging,
                }
            )
        details["pooled_manifest"] = loads
        details["total_manifest_tonnes"] = sum(load["weight_tonnes"] for load in loads)
    if kind == "proof-of-delivery":
        from sqlalchemy import select
        from backend.models import Shipment

        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
        details["proof"] = shipment.operational_data
        details["delivery_confirmed"] = shipment.status == "DELIVERED"
    if vessel:
        details["approved_route"] = booking.plan_snapshot.get("route")
        details["navigation_notice"] = (
            "Consult verified authority notices before real navigation. This demo is not a navigation aid."
        )
    return details
