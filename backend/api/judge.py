from fastapi import APIRouter, Depends, HTTPException
from typing import Literal
from pydantic import Field
from backend.database import get_db
from backend.auth import get_actor
from backend.api.demo import demo_permission
from backend.models import *
from backend.schemas.requests import (
    StrictModel,
    CargoCreate,
    BookingCreate,
    RecoveryApproval,
)
from backend.repositories.common import uid, record, audit, require
from backend.services.bookings import create_booking, transition
from backend.services.recovery import disrupt, approve_pool_recovery
from backend.services.impact import calculate_impact
from intelligence.voice_intake.parser import parse_voice, DEMO_TRANSCRIPT
from intelligence.document_intake.parser import parse_cargo
from optimization.matching.engine import match
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul

router = APIRouter(prefix="/api/demo/judge", tags=["guided judge demo"])


class JudgeStep(StrictModel):
    stage: Literal[
        "VOICE",
        "CARGO",
        "FEASIBILITY",
        "OPTIMIZATION",
        "BOOK",
        "RECOVERY",
        "START",
        "IMPACT",
    ]
    approved: bool = False
    vessel_id: str | None = None


@router.post("/step")
async def step(payload: JudgeStep, db=Depends(get_db), actor=Depends(get_actor)):
    demo_permission(actor)
    session = db.get(JudgeSession, "judge-session")
    if not session:
        session = JudgeSession(id="judge-session", state={})
        db.add(session)
        db.flush()
    state = dict(session.state)
    stage = payload.stage
    if stage in state.get("completed", []):
        raise HTTPException(
            409, "This checkpoint is already complete. Reset for another story."
        )
    result = {}
    if stage == "VOICE":
        extraction = await parse_voice(
            DEMO_TRANSCRIPT, "demo_transcript_not_audio_transcription"
        )
        availability = require(db, VesselAvailability, "availability-vembanad")
        result = {
            "extraction": extraction,
            "window": {
                "available_from": availability.available_from,
                "available_until": availability.available_until,
            },
            "requires_confirmation": True,
            "explanation": "Disclosed offline transcript. Exact operating window is supplied for operator review.",
        }
        if payload.approved:
            fields = extraction["fields"]
            vessel = require(db, Vessel, "vembanad")
            if (
                any(
                    fields[key] is None
                    for key in ["origin", "destination", "capacity_tonnes"]
                )
                or fields["capacity_tonnes"] > vessel.max_capacity_tonnes
            ):
                raise HTTPException(
                    409, "Review missing/invalid voice fields manually."
                )
            item = VesselAvailability(
                id=uid("judge-availability"),
                vessel_id=vessel.id,
                origin=fields["origin"],
                destination=fields["destination"],
                capacity_tonnes=fields["capacity_tonnes"],
                volume_m3=vessel.max_volume_m3,
                available_from=availability.available_from,
                available_until=availability.available_until,
            )
            db.add(item)
            audit(db, "vessel.available", vessel.id, actor, availability_id=item.id)
            state["availability_id"] = item.id
    elif stage == "CARGO":
        if "availability_id" not in state:
            raise HTTPException(409, "Confirm operator availability first.")
        hero = require(db, CargoRequest, "hero-cargo")
        text = f"80 tonnes cement bagged, 60 m3, from Kalamassery to Alappuzha. Ready {hero.ready_time}; deliver by {hero.delivery_deadline}. Non-hazardous."
        extraction = await parse_cargo(text)
        result = {
            "extraction": extraction,
            "requires_confirmation": True,
            "explanation": "Extraction is reviewed before creating a real cargo request.",
        }
        if payload.approved:
            # Operator/shipper explicitly confirms local safety options and connection legs.
            fields = {
                key: value
                for key, value in extraction["fields"].items()
                if value is not None
            }
            fields.update(
                {
                    "ready_time": hero.ready_time,
                    "delivery_deadline": hero.delivery_deadline,
                    "first_mile_required": True,
                    "last_mile_required": False,
                }
            )
            validated = CargoCreate.model_validate(fields)
            cargo = CargoRequest(
                id=uid("judge-cargo"),
                organization_id="shipper-org",
                **validated.model_dump(mode="json"),
            )
            db.add(cargo)
            audit(
                db,
                "cargo.created",
                cargo.id,
                actor,
                source="Confirmed guided demo extraction",
            )
            state["cargo_id"] = cargo.id
    else:
        cargo = require(
            db, CargoRequest, state.get("cargo_id", "missing-confirmed-cargo")
        )
        if stage == "FEASIBILITY":
            result = match(db, cargo, persist=True, actor=actor)
            from backend.services.planning import compare_modes

            result["mode_comparison"] = compare_modes(db, cargo, "vembanad")
        elif stage == "OPTIMIZATION":
            pool = optimize_pool(
                db,
                cargo,
                require(db, Vessel, "vembanad"),
                organization_id=cargo.organization_id,
                actor=actor,
            )
            backhaul = find_backhaul(
                db, cargo, require(db, Vessel, "vembanad"), actor=actor
            )
            state["pool_id"] = pool["pool"]["id"]
            result = {"pooling": pool, "backhaul": backhaul}
        elif stage == "BOOK":
            if not state.get("pool_id"):
                raise HTTPException(409, "Calculate and inspect the pool first.")
            if payload.approved:
                result = create_booking(
                    db,
                    actor,
                    BookingCreate(
                        cargo_id=cargo.id,
                        vessel_id="vembanad",
                        pool_id=state["pool_id"],
                        mode="HYBRID",
                        approved=True,
                    ),
                )
                state["booking_id"] = result["booking"]["id"]
                state["shipment_ids"] = [
                    item["shipment"]["id"] for item in result["bookings"]
                ]
            else:
                pool = require(db, PoolingGroup, state["pool_id"])
                result = {
                    "pool": record(pool),
                    "requires_confirmation": True,
                    "explanation": "Approve both pooled cargo bookings after reviewing feasibility and delivered prices.",
                }
        elif stage == "RECOVERY":
            booking = require(db, Booking, state.get("booking_id", "missing-booking"))
            if not state.get("recovery_preview"):
                result = disrupt(db, actor, booking, "VESSEL_UNAVAILABLE")
                state["recovery_preview"] = result
            else:
                result = state["recovery_preview"]
            if payload.approved:
                requested = payload.vessel_id
                option = next(
                    (
                        option
                        for option in result["alternatives"]
                        if option["vessel_id"] == requested
                    ),
                    None,
                )
                if not option:
                    raise HTTPException(
                        422, "Select a previously shown recovery option."
                    )
                result = approve_pool_recovery(
                    db,
                    actor,
                    booking,
                    RecoveryApproval(
                        vessel_id=option["vessel_id"],
                        mode=option["mode"],
                        approved=True,
                    ),
                )
        elif stage == "START":
            if not state.get("shipment_ids"):
                raise HTTPException(409, "Approve a booking before departure.")
            if not payload.approved:
                result = {
                    "requires_confirmation": True,
                    "shipment_count": len(state["shipment_ids"]),
                    "explanation": "Confirm scheduled, loading and departure milestones for the pooled voyage.",
                }
            else:
                result = {"shipments": []}
                for key in state["shipment_ids"]:
                    shipment = require(db, Shipment, key)
                    for milestone in ["SCHEDULED", "LOADING", "IN_TRANSIT"]:
                        if shipment.status == milestone:
                            continue
                        if milestone == "SCHEDULED" and shipment.status == "SCHEDULED":
                            continue
                        transition(db, actor, shipment, milestone)
                    result["shipments"].append(record(shipment))
        elif stage == "IMPACT":
            result = calculate_impact(db)
    confirmation_stages = {"VOICE", "CARGO", "BOOK", "RECOVERY", "START"}
    complete = stage not in confirmation_stages or payload.approved
    if stage == "RECOVERY" and not payload.vessel_id:
        complete = False
    if complete:
        state["completed"] = [*state.get("completed", []), stage]
    state["last_stage"] = stage
    session.state = state
    audit(
        db,
        "judge.checkpoint",
        stage,
        actor,
        approved=payload.approved,
        complete=complete,
    )
    db.commit()
    return {
        "stage": stage,
        "complete": complete,
        "result": result,
        "completed": state.get("completed", []),
        "source": "Real application services and persisted transactions; synthetic inputs, no static screenshot substitution",
    }
