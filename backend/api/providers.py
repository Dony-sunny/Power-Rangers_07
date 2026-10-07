from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.auth import get_actor, permission
from backend.database import get_db
from backend.repositories.common import require
from backend.models import Vessel, Shipment, Booking
from sqlalchemy import select
from fastapi import Query
from backend.services.connectors import (
    ExternalTrackingProvider,
    ExternalWeatherProvider,
    connector_status,
)
from intelligence.provider.llm import (
    provider,
    ProviderUnavailable,
    diagnostics,
    PROVIDER_STATE,
)

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/diagnostics")
def status(actor=Depends(get_actor)):
    permission(actor, "demo_admin")
    return {**diagnostics(), "connectors": connector_status()}


class Probe(BaseModel):
    ok: bool


@router.post("/diagnostics")
async def probe(actor=Depends(get_actor)):
    permission(actor, "demo_admin")
    try:
        result = Probe.model_validate(
            await provider.structured(
                'Return {"ok":true}. This is a connection test.',
                Probe.model_json_schema(),
            )
        )
        PROVIDER_STATE["llm"] = "connected" if result.ok else "unavailable"
    except (ProviderUnavailable, ValueError):
        PROVIDER_STATE["llm"] = "unavailable"
    return {**diagnostics(), "connectors": connector_status()}


@router.get("/tracking/{vessel_id}")
async def position(vessel_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    vessel = require(db, Vessel, vessel_id)
    if (
        actor.role_id not in {"admin", "control", "network", "government"}
        and vessel.organization_id != actor.organization_id
    ):
        from backend.services.bookings import booking_access

        assigned = False
        for booking in db.scalars(
            select(Booking).where(Booking.vessel_id == vessel_id)
        ):
            try:
                booking_access(db, actor, booking)
                assigned = True
                break
            except HTTPException:
                pass
        if not assigned:
            raise HTTPException(404, "Assigned vessel not found.")
    shipment = db.scalar(
        select(Shipment)
        .join(Booking, Shipment.booking_id == Booking.id)
        .where(Booking.vessel_id == vessel_id)
        .order_by(Booking.created_at.desc())
    )
    from optimization.multimodal.costs import coordinates

    lat, lon = (
        (shipment.latitude, shipment.longitude)
        if shipment
        else coordinates(vessel.current_location)
    )
    return await ExternalTrackingProvider().position(vessel.id, lat, lon)


@router.get("/weather")
async def weather(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    actor=Depends(get_actor),
):
    return await ExternalWeatherProvider().weather(latitude, longitude)
