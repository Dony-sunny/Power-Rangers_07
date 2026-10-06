from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from backend.database import get_db
from backend.auth import get_actor, permission
from backend.models import CargoDocument
from backend.repositories.common import uid, record
from backend.schemas.requests import TextIntake, CargoCreate
from intelligence.document_intake.parser import parse_cargo
from intelligence.document_intake.documents import (
    read_upload,
    document_text,
    csv_preview,
)
from intelligence.voice_intake.parser import parse_voice, transcribe, DEMO_TRANSCRIPT
from intelligence.provider.llm import ProviderUnavailable

router = APIRouter(prefix="/api/intake", tags=["intake"])


@router.post("/cargo/text")
async def cargo_text(payload: TextIntake, actor=Depends(get_actor)):
    permission(actor, "cargo_write")
    return await parse_cargo(payload.text)


@router.post("/cargo/document")
async def cargo_document(
    file: UploadFile = File(...), db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "cargo_write")
    content, filename, suffix = await read_upload(file)
    image = suffix in {".png", ".jpg", ".jpeg"}
    if image and not (
        content.startswith(b"\x89PNG\r\n\x1a\n") or content.startswith(b"\xff\xd8\xff")
    ):
        raise HTTPException(415, "Image file signature is invalid.")
    text = "" if image else document_text(content, suffix)
    extraction = await parse_cargo(
        text,
        content if image else None,
        "image/png" if suffix == ".png" else "image/jpeg",
    )
    if not text and not image:
        extraction["warnings"].append(
            "No extractable text: scanned PDFs need OCR/multimodal integration. Enter missing fields manually."
        )
    document = CargoDocument(
        id=uid("document"),
        organization_id=actor.organization_id,
        cargo_id=None,
        filename=filename,
        mime_type=file.content_type or "application/octet-stream",
        extracted_text=text,
        extraction=extraction,
    )
    db.add(document)
    db.commit()
    return {**extraction, "document_id": document.id, "filename": filename}


@router.post("/cargo/bulk-preview")
async def bulk_preview(file: UploadFile = File(...), actor=Depends(get_actor)):
    permission(actor, "cargo_write")
    content, _, suffix = await read_upload(file)
    if suffix != ".csv":
        raise HTTPException(
            415, "Bulk preview accepts CSV. XLSX conversion is an extension point."
        )
    results = []
    from pydantic import ValidationError

    for index, row in enumerate(csv_preview(content)):
        row = {k: v for k, v in row.items() if v != ""}
        try:
            parsed = CargoCreate.model_validate(row)
            results.append(
                {
                    "row": index + 2,
                    "valid": True,
                    "fields": parsed.model_dump(mode="json"),
                }
            )
        except ValidationError as error:
            results.append(
                {
                    "row": index + 2,
                    "valid": False,
                    "errors": error.errors(include_url=False, include_context=False),
                }
            )
    return {"rows": results, "requires_confirmation": True, "saved": False}


@router.post("/vessel/text")
async def vessel_text(payload: TextIntake, actor=Depends(get_actor)):
    permission(actor, "availability_write")
    return await parse_voice(payload.text)


@router.post("/vessel/audio")
async def vessel_audio(
    file: UploadFile = File(...),
    use_demo_transcript: bool = Form(False),
    actor=Depends(get_actor),
):
    permission(actor, "availability_write")
    content, filename, suffix = await read_upload(file)
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".webm"}:
        raise HTTPException(415, "Audio uploads: WAV, MP3, M4A, OGG or WEBM.")
    try:
        transcript, source = await transcribe(
            content, filename, file.content_type or "audio/webm", use_demo_transcript
        )
    except ProviderUnavailable as error:
        raise HTTPException(503, str(error)) from None
    return await parse_voice(transcript, source)


@router.post("/vessel/demo")
async def vessel_demo(actor=Depends(get_actor)):
    from backend.config import settings

    permission(actor, "availability_write")
    if not settings.demo_mode:
        raise HTTPException(403, "Demo transcript is disabled.")
    return await parse_voice(DEMO_TRANSCRIPT, "demo_transcript_not_audio_transcription")
