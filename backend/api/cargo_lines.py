from datetime import datetime
import math
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, model_validator
from sqlalchemy import select
from backend.database import get_db
from backend.auth import get_actor, cargo_access, permission
from backend.models import *
from backend.schemas.requests import StrictModel, CargoCreate
from backend.repositories.common import require, uid, record, audit
from backend.services import cargo_lines as lines
from backend.services.line_planning import build_plan, loaded_cargo
from backend.services.timeutils import dt
from backend.services.bookings import lock_writes, _active_for_cargo
from optimization.multimodal.costs import road_plan
from optimization.multimodal.trip_costs import TERMS

router = APIRouter(prefix="/api/lines", tags=["three-role Cargo Lines"])


class Proposal(StrictModel):
    cargo_ids: list[str] = Field(min_length=1, max_length=20)
    vessel_id: str
    parent_id: str | None = None
    not_before: datetime | None = None
    availability_id: str | None = None

    @model_validator(mode="after")
    def unique(self):
        if self.not_before and self.not_before.tzinfo is None:
            raise ValueError("Preferred departure needs a timezone offset.")
        if len(self.cargo_ids) != len(set(self.cargo_ids)):
            raise ValueError("Each cargo can appear only once.")
        return self


class OperatorResponse(StrictModel):
    version: int = Field(ge=1)
    accept: bool
    acknowledge_shortfall: bool = False


class JobResponse(StrictModel):
    status: str = Field(pattern="^(ACCEPTED|DECLINED)$")


class Cancellation(StrictModel):
    cargo_id: str | None = None


class Milestone(StrictModel):
    status: str = Field(pattern="^(SCHEDULED|LOADING|IN_TRANSIT|UNLOADING)$")


class Receipt(StrictModel):
    cargo_id: str
    quantity_tonnes: float = Field(gt=0, le=10000, allow_inf_nan=False)
    receiver_name: str = Field(min_length=2, max_length=100)


class LoadProfile(StrictModel):
    heaviest_piece_tonnes: float = Field(gt=0, le=1000, allow_inf_nan=False)
    unit_length_m: float = Field(default=1, gt=0, le=100, allow_inf_nan=False)
    unit_width_m: float = Field(default=1, gt=0, le=100, allow_inf_nan=False)
    unit_height_m: float = Field(default=1, gt=0, le=100, allow_inf_nan=False)
    pieces: int = Field(ge=1, le=1000000)
    receiving_from: datetime | None = None
    receiving_until: datetime | None = None

    @model_validator(mode="after")
    def window(self):
        if any(value and value.tzinfo is None for value in [self.receiving_from, self.receiving_until]):
            raise ValueError("Receiving windows need timezone offsets.")
        if self.receiving_from and self.receiving_until and self.receiving_from >= self.receiving_until:
            raise ValueError("Receiving window must be ordered.")
        return self


class MarketplaceCargo(StrictModel):
    cargo: CargoCreate
    load_profile: LoadProfile

    @model_validator(mode="after")
    def piece_capacity(self):
        profile, cargo = self.load_profile, self.cargo
        if cargo.volume_m3 is None:
            raise ValueError("Cargo volume is required to compare boats and schedule delivery.")
        if profile.heaviest_piece_tonnes > cargo.weight_tonnes or profile.heaviest_piece_tonnes * profile.pieces + 1e-9 < cargo.weight_tonnes:
            raise ValueError("Piece count and heaviest piece cannot contain the stated weight.")
        return self


@router.post("/cargo", status_code=201)
def marketplace_cargo(payload: MarketplaceCargo, db=Depends(get_db), actor=Depends(get_actor)):
    """Publish cargo and its reviewed load profile in one transaction."""
    permission(actor, "cargo_write")
    lock_writes(db)
    cargo = CargoRequest(id=uid("cargo"), organization_id=actor.organization_id,
                         **payload.cargo.model_dump(mode="json"))
    db.add(cargo)
    db.flush()
    db.add(CargoLoadProfile(id=uid("profile"), cargo_id=cargo.id,
                           **payload.load_profile.model_dump(mode="json")))
    audit(db, "cargo.created", cargo.id, actor, weight_tonnes=cargo.weight_tonnes)
    audit(db, "line.load_profile_reviewed", cargo.id, actor)
    db.commit()
    return record(cargo)


@router.get("")
def workspace(db=Depends(get_db), actor=Depends(get_actor)):
    # Existing team identities retain their scoped operational access beneath
    # the three customer-facing workspaces. Approval permissions stay separate.
    lines.expire(db)
    db.commit()
    result = []
    for voyage in db.scalars(select(CargoVoyage).order_by(CargoVoyage.created_at.desc())):
        try:
            result.append(lines.serialize(db, actor, voyage))
        except HTTPException:
            continue
    return {"departures": result, "impact": lines.impact(db, actor) if actor.role_id == "control" else None, "tariff": TERMS, "source": "SIMULATED"}


@router.get("/cargo/{cargo_id}/profile")
def profile(cargo_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    value = db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == cargo_id))
    return {"profile": record(value) if value else None}


@router.post("/cargo/{cargo_id}/profile")
def save_profile(cargo_id: str, payload: LoadProfile, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "cargo_write")
    lock_writes(db)
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    if _active_for_cargo(db, cargo_id):
        raise HTTPException(409, "Accepted cargo requires an approved amendment; its load profile is locked.")
    if payload.heaviest_piece_tonnes > cargo.weight_tonnes or payload.heaviest_piece_tonnes * payload.pieces + 1e-9 < cargo.weight_tonnes:
        raise HTTPException(422, "Piece count and heaviest piece cannot contain the stated weight.")
    value = db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == cargo_id))
    if not value:
        value = CargoLoadProfile(id=uid("profile"), cargo_id=cargo_id, **payload.model_dump(mode="json"))
        db.add(value)
    else:
        for key, field in payload.model_dump(mode="json").items():
            setattr(value, key, field)
    audit(db, "line.load_profile_reviewed", cargo_id, actor)
    db.commit()
    return record(value)


@router.get("/cargo/{cargo_id}/advice")
def advice(cargo_id: str, vessel_id: str, crossover: bool = False, not_before: datetime | None = None, availability_id: str | None = None, db=Depends(get_db), actor=Depends(get_actor)):
    if not_before and not_before.tzinfo is None:
        raise HTTPException(422, "Preferred departure needs a timezone offset.")
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    vessel = require(db, Vessel, vessel_id)
    item = loaded_cargo(db, cargo)
    road = road_plan(item)
    water, reasons = None, []
    try:
        plan = build_plan(db, [item], vessel, not_before=not_before, pinned_availability_id=availability_id)
        water = plan["members"][0]
        water["projected_economics"] = plan["economics"]
    except HTTPException as error:
        reasons = error.detail if isinstance(error.detail, list) else error.detail.get("reasons", [error.detail.get("message")]) if isinstance(error.detail, dict) else [error.detail]
    candidates = [p for p in [road, water] if p and p.get("feasible")]
    best = min(candidates, key=lambda p: p["total_cost"]) if candidates else None
    samples, ranges = [], []
    if crossover and hasattr(item, "heaviest_piece_tonnes") and item.volume_m3:
        from types import SimpleNamespace
        maximum = min(150, math.floor(vessel.max_capacity_tonnes), math.floor(vessel.max_volume_m3 * item.weight_tonnes / item.volume_m3))
        for weight in range(1, maximum + 1):
            trial = SimpleNamespace(**vars(item))
            trial.weight_tonnes, trial.volume_m3, trial.budget = weight, item.volume_m3 * weight / item.weight_tonnes, None
            trial.pieces = max(1, math.ceil(item.pieces * weight / item.weight_tonnes))
            if weight < item.heaviest_piece_tonnes:
                continue
            try:
                candidate = build_plan(db, [trial], vessel, not_before=not_before, pinned_availability_id=availability_id)["members"][0]
                baseline = road_plan(trial)
                if baseline["feasible"] and candidate["total_cost"] < baseline["total_cost"]:
                    samples.append(weight)
            except HTTPException:
                pass
        for weight in samples:
            if ranges and weight == ranges[-1][1] + 1:
                ranges[-1][1] = weight
            else:
                ranges.append([weight, weight])
    return {"road": road, "water": water, "water_rejection_reasons": reasons, "recommended_mode": best["mode"] if best else None,
        "crossover_ranges_tonnes": ranges if crossover else None,
        "crossover_basis": "1-tonne sampled feasible scenarios, maximum 150 t, proportional volume/pieces, same endpoints/deadline. These are sampled ranges, not a continuous or universal threshold.",
        "source": TERMS["source"], "tariff": TERMS}


@router.post("/proposals", status_code=201)
def proposal(payload: Proposal, db=Depends(get_db), actor=Depends(get_actor)):
    if payload.parent_id:
        parent = require(db, CargoVoyage, payload.parent_id)
        lines.coordinate(actor, parent)
        expected = {m.cargo_id for m in lines.members(db, parent) if m.status == "DISRUPTED"}
        if parent.status != "DISRUPTED" or set(payload.cargo_ids) != expected:
            raise HTTPException(409, "Replacement must contain every disrupted consignment.")
    return lines.propose(db, actor, payload.cargo_ids, payload.vessel_id, payload.parent_id, payload.not_before, payload.availability_id)


@router.post("/quotes/{quote_id}/approve")
def approve(quote_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.approve_quote(db, actor, quote_id)


@router.post("/{voyage_id}/operator-response")
def operator(voyage_id: str, payload: OperatorResponse, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.operator_response(db, actor, voyage_id, payload.version, payload.accept, payload.acknowledge_shortfall)


@router.post("/jobs/{job_id}/response")
def provider(job_id: str, payload: JobResponse, db=Depends(get_db), actor=Depends(get_actor)):
    from backend.config import settings
    if not settings.demo_mode:
        raise HTTPException(503, "Local provider simulator is available only in demo mode.")
    return lines.job_response(db, actor, job_id, payload.status)


@router.post("/{voyage_id}/confirm")
def confirm(voyage_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.confirm(db, actor, voyage_id)


@router.post("/{voyage_id}/cancel")
def cancel(voyage_id: str, payload: Cancellation, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.cancel(db, actor, voyage_id, payload.cargo_id)


@router.post("/{voyage_id}/milestone")
def milestone(voyage_id: str, payload: Milestone, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.milestones(db, actor, voyage_id, payload.status)


@router.post("/{voyage_id}/receipt")
def receipt(voyage_id: str, payload: Receipt, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.receipt(db, actor, voyage_id, payload.cargo_id, payload.quantity_tonnes, payload.receiver_name)


@router.post("/{voyage_id}/disrupt")
def disrupt(voyage_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.disrupt(db, actor, voyage_id)


@router.get("/{voyage_id}/recovery-options")
def recovery(voyage_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    return lines.recovery_options(db, actor, require(db, CargoVoyage, voyage_id))
