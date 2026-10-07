from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from pydantic import Field
from backend.database import get_db
from backend.auth import get_actor
from backend.models import EvidencePhoto, LabelReference
from backend.schemas.requests import StrictModel
from backend.repositories.common import require
from backend.services.evidence import *
from intelligence.document_intake.documents import read_upload

router = APIRouter(prefix="/api", tags=["evidence and delivery verification"])


@router.post("/shipments/{shipment_id}/photos", status_code=201)
async def upload_photo(
    shipment_id: str,
    file: UploadFile = File(...),
    category: str = Form("HANDOVER"),
    description: str = Form(""),
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    content, filename, suffix = await read_upload(file)
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(415, "Evidence accepts PNG/JPEG only.")
    return save_photo(db, actor, shipment_id, content, category, description)


@router.get("/shipments/{shipment_id}/photos")
def photos(shipment_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    shipment_access(db, actor, shipment_id)
    return {
        "photos": [
            photo_metadata(photo)
            for photo in db.scalars(
                select(EvidencePhoto).where(EvidencePhoto.shipment_id == shipment_id)
            )
        ]
    }


@router.get("/photos/{photo_id}")
def photo(photo_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    item = require(db, EvidencePhoto, photo_id)
    shipment_access(db, actor, item.shipment_id)
    return {
        **photo_metadata(item),
        "data_url": f"data:{item.mime_type};base64,{item.image_base64}",
    }


@router.get("/labels/{kind}/{entity_id}/print")
def label_print(
    kind: str, entity_id: str, db=Depends(get_db), actor=Depends(get_actor)
):
    return Response(
        printable_label(make_label(db, actor, kind, entity_id)),
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="jalayatra-label.html"'},
    )


@router.get("/labels/{kind}/{entity_id}")
def label(kind: str, entity_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    return make_label(db, actor, kind, entity_id)


@router.get("/labels/{reference}")
def resolve_label(reference: str, db=Depends(get_db), actor=Depends(get_actor)):
    item = require(db, LabelReference, reference)
    return label_entity(db, actor, item.entity_type, item.entity_id)


@router.post("/shipments/{shipment_id}/delivery-challenge")
def challenge(shipment_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    return request_challenge(db, actor, shipment_id)


class OTPVerify(StrictModel):
    code: str = Field(pattern=r"^\d{6}$")


@router.post("/delivery-challenges/{challenge_id}/verify")
def verify(
    challenge_id: str, payload: OTPVerify, db=Depends(get_db), actor=Depends(get_actor)
):
    return verify_challenge(db, actor, challenge_id, payload.code)
