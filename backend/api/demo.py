from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select, delete
from backend.database import get_db, Base
from backend.config import settings
from backend.auth import get_actor, permission
from backend.schemas.requests import StrictModel, BookingCreate, TextIntake
from backend.models import *
from backend.repositories.common import record, audit
from backend.services.bookings import create_booking
from backend.services.recovery import disrupt
from backend.services.impact import calculate_impact
from data.seed.network import seed
from optimization.matching.engine import match
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from intelligence.broker_agent.agent import broker

router = APIRouter(prefix="/api", tags=["broker and demo"])


class BrokerRequest(TextIntake):
    cargo_id: str | None = None


@router.post("/broker")
async def broker_request(
    payload: BrokerRequest, db=Depends(get_db), actor=Depends(get_actor)
):
    return await broker(db, actor, payload.text, payload.cargo_id)


class DemoScenario(StrictModel):
    scenario: str = Field(pattern="^[ABCDEF]$")


def demo_permission(actor):
    permission(actor, "demo_admin")
    if not settings.demo_mode:
        raise HTTPException(403, "Demo controls are disabled outside DEMO_MODE.")


@router.post("/demo/reset")
def reset(db=Depends(get_db), actor=Depends(get_actor)):
    demo_permission(actor)
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(delete(table))
    db.commit()
    db.expunge_all()
    seed(db)
    from backend.services.terminal_resources import seed_resources

    seed_resources(db)
    audit(db, "demo.reset", "demo", None)
    db.commit()
    return {
        "status": "reset",
        "source": "Fresh synthetic fixtures; previous demo transactions removed.",
    }


@router.post("/demo/populate")
def populate_marketplace(db=Depends(get_db), actor=Depends(get_actor)):
    demo_permission(actor)
    from backend.services.marketplace_demo import populate
    return populate(db)


@router.post("/demo/scenario")
def scenario(payload: DemoScenario, db=Depends(get_db), actor=Depends(get_actor)):
    demo_permission(actor)
    cargo = db.get(CargoRequest, "hero-cargo")
    vessel = db.get(Vessel, "vembanad")
    name = payload.scenario
    if name == "B":
        return match(db, cargo, persist=True, actor=actor)
    if name == "C":
        return optimize_pool(db, cargo, vessel, actor=actor)
    if name == "D":
        return find_backhaul(db, cargo, vessel, actor=actor)
    if name == "F":
        from backend.services.demo_state import flood_enabled

        enabled = not flood_enabled(db)
        audit(db, "demo.flood", "road-corridor", actor, enabled=enabled)
        for item in db.scalars(select(CargoRequest)):
            if item.status in {"POSTED", "MATCHED", "QUOTED"}:
                item.priority = "CRITICAL" if enabled else "NORMAL"
        db.commit()
        return {
            "flood_simulated": enabled,
            "impact": calculate_impact(db),
            "notice": "Simulated road disruption; no IMD/government integration.",
        }
    existing = db.scalar(
        select(Booking).where(
            Booking.cargo_id == cargo.id, Booking.status.not_in(["CANCELLED", "FAILED"])
        )
    )
    result = None
    if not existing:
        result = create_booking(
            db,
            actor,
            BookingCreate(
                cargo_id=cargo.id, vessel_id=vessel.id, mode="HYBRID", approved=True
            ),
        )
        existing = db.get(Booking, result["booking"]["id"])
    if name == "E":
        return disrupt(db, actor, existing, "VESSEL_UNAVAILABLE")
    return result or {"booking": record(existing)}
