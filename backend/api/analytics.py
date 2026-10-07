import base64
from datetime import timedelta
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from pydantic import Field
from typing import Literal
from backend.auth import get_actor, permission, cargo_access
from backend.database import get_db
from backend.models import *
from backend.repositories.common import uid, require, record, audit
from backend.schemas.requests import StrictModel
from backend.services.analytics import (
    corridor_reliability,
    rate_benchmark,
    failed_demand,
    historical_modal_shift,
)
from backend.services.timeutils import utcnow, dt
from intelligence.document_intake.documents import read_upload
from intelligence.document_intake.spreadsheets import preview_rows
from intelligence.document_intake.ocr import validate_image

router = APIRouter(prefix="/api", tags=["network intelligence"])


@router.get("/intelligence/corridors")
def corridors(db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id not in {
        "government",
        "network",
        "control",
        "admin",
        "operator",
        "fleet",
    }:
        raise HTTPException(403, "Corridor analytics requires network/operator access.")
    return corridor_reliability(db)


@router.get("/intelligence/failed-demand")
def unmet(db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "metrics")
    return failed_demand(db)


@router.get("/cargo/{cargo_id}/rate-benchmark")
def rates(
    cargo_id: str,
    vessel_id: str | None = None,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    from backend.services.planning import compare_modes

    comparison = compare_modes(db, cargo, vessel_id)
    plan = next(
        (
            p
            for p in comparison["plans"]
            if p["feasible"] and p["mode"] == comparison["recommended_mode"]
        ),
        None,
    )
    return rate_benchmark(db, cargo, plan["total_cost"] if plan else None)


@router.post("/cargo/{cargo_id}/reject-quote")
def reject(cargo_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    db.add(
        DemandSearch(
            id=uid("search"),
            cargo_id=cargo.id,
            outcome="PRICE_REJECTED",
            reasons=["PRICE_REJECTED"],
        )
    )
    audit(db, "quote.price_rejected", cargo.id, actor)
    db.commit()
    return {"reason": "PRICE_REJECTED", "cargo_id": cargo.id}


@router.post("/intelligence/modal-shift/upload")
async def history(
    file: UploadFile = File(...), db=Depends(get_db), actor=Depends(get_actor)
):
    if actor.role_id not in {"government", "network", "control", "admin", "shipper"}:
        raise HTTPException(403, "Modal-shift analysis requires planning access.")
    content, filename, suffix = await read_upload(file)
    from starlette.concurrency import run_in_threadpool

    rows = await run_in_threadpool(preview_rows, content, suffix)
    result = await run_in_threadpool(historical_modal_shift, db, rows)
    audit(
        db,
        "modal_shift.analyzed",
        filename,
        actor,
        valid_rows=result["total_shipments_analyzed"],
    )
    db.commit()
    return result


class ReportReview(StrictModel):
    verification_status: Literal["VERIFIED", "DISPUTED"]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    note: str = Field(min_length=3, max_length=1000)
    promote_restriction: bool = False


@router.patch("/reports/{report_id}")
def review(
    report_id: str, payload: ReportReview, db=Depends(get_db), actor=Depends(get_actor)
):
    if actor.role_id not in {"network", "admin"}:
        raise HTTPException(403, "Network control reviews operator observations.")
    report = require(db, NavigationReport, report_id)
    if dt(report.expires_at) <= utcnow():
        raise HTTPException(409, "Expired reports cannot create a restriction.")
    if payload.promote_restriction and payload.verification_status != "VERIFIED":
        raise HTTPException(
            422, "Only explicitly verified observations may be promoted."
        )
    report.verification_status = payload.verification_status
    report.confidence = payload.confidence
    restriction = None
    if payload.promote_restriction:
        restriction = RouteRestriction(
            id=uid("restriction"),
            segment_id=report.segment_id,
            reason=f"Platform-reviewed operator observation: {payload.note}",
            starts_at=utcnow().isoformat(),
            ends_at=report.expires_at,
        )
        db.add(restriction)
    audit(
        db,
        "navigation.report_reviewed",
        report.id,
        actor,
        status=payload.verification_status,
        note=payload.note,
        promoted=payload.promote_restriction,
    )
    db.commit()
    return {
        **record(report),
        "restriction_id": restriction.id if restriction else None,
        "source": "Platform review of user observations, not official navigation authority data",
    }


@router.post("/reports/{report_id}/photos", status_code=201)
async def report_photo(
    report_id: str,
    file: UploadFile = File(...),
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "report")
    report = require(db, NavigationReport, report_id)
    if report.reporter_id != actor.id and actor.role_id not in {"network", "admin"}:
        raise HTTPException(404, "Report not found.")
    content, filename, suffix = await read_upload(file)
    if suffix not in {".png", ".jpg", ".jpeg"} or len(content) > 2 * 1024 * 1024:
        raise HTTPException(415, "Report photos accept PNG/JPEG up to 2 MB.")
    image = validate_image(content)
    image.thumbnail((1600, 1600))
    out = BytesIO()
    image.save(out, "JPEG", quality=85)
    item = NavigationPhoto(
        id=uid("report-photo"),
        report_id=report_id,
        uploader_id=actor.id,
        image_base64=base64.b64encode(out.getvalue()).decode(),
    )
    db.add(item)
    audit(db, "navigation.photo_saved", item.id, actor)
    db.commit()
    return {"photo_id": item.id, "report_id": report_id}


@router.get("/reports/{report_id}/photos")
def report_photos(report_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "report")
    require(db, NavigationReport, report_id)
    return {
        "photos": [
            {
                "id": item.id,
                "created_at": item.created_at,
                "data_url": "data:image/jpeg;base64," + item.image_base64,
            }
            for item in db.scalars(
                select(NavigationPhoto).where(NavigationPhoto.report_id == report_id)
            )
        ]
    }
