from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from backend.database import get_db
from backend.auth import get_actor, permission
from backend.models import CargoDocument, BulkImport, CargoRequest
from backend.repositories.common import uid, record, require, audit
from backend.services.timeutils import utcnow, dt
from datetime import timedelta
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from intelligence.document_intake.ocr import validate_image, run_ocr
from intelligence.document_intake.spreadsheets import (
    preview_rows,
    template_bytes,
    error_csv,
)
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
    if image:
        validate_image(content)
    text = "" if image else await run_in_threadpool(document_text, content, suffix)
    recognition = None
    if image or suffix == ".pdf" and len(text.strip()) < 25:
        recognition = await run_in_threadpool(run_ocr, content, suffix)
        text = recognition["text"]
    extraction = await parse_cargo(
        text,
        content if image and not text else None,
        "image/png" if suffix == ".png" else "image/jpeg",
    )
    if recognition:
        extraction["document_recognition"] = {
            k: v for k, v in recognition.items() if k != "text"
        }
        extraction["warnings"].extend(recognition["warnings"])
        extraction["extracted_text_preview"] = text[:1500]
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
async def bulk_preview(
    file: UploadFile = File(...), db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "cargo_write")
    content, _, suffix = await read_upload(file)
    results = await run_in_threadpool(preview_rows, content, suffix)
    batch = BulkImport(
        id=uid("import"), organization_id=actor.organization_id, rows=results
    )
    db.add(batch)
    db.commit()
    return {
        "rows": results,
        "preview_id": batch.id,
        "valid_count": sum(r["valid"] for r in results),
        "invalid_count": sum(not r["valid"] for r in results),
        "requires_confirmation": True,
        "saved": False,
    }


@router.get("/cargo/bulk-template")
def bulk_template(actor=Depends(get_actor)):
    permission(actor, "cargo_write")
    return Response(
        template_bytes(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="jalayatra-cargo-template.xlsx"'
        },
    )


@router.get("/cargo/bulk-preview/{preview_id}/errors")
def bulk_errors(preview_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "cargo_write")
    batch = require(db, BulkImport, preview_id)
    if batch.organization_id != actor.organization_id:
        raise HTTPException(404, "Preview not found.")
    return Response(
        error_csv(batch.rows),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="import-errors.csv"'},
    )


@router.post("/cargo/bulk-import/{preview_id}", status_code=201)
def bulk_import(
    preview_id: str,
    approved: bool = False,
    db=Depends(get_db),
    actor=Depends(get_actor),
):
    permission(actor, "cargo_write")
    if not approved:
        raise HTTPException(422, "Approve valid rows before import.")
    from backend.services.bookings import lock_writes

    lock_writes(db)
    batch = require(db, BulkImport, preview_id)
    if batch.organization_id != actor.organization_id:
        raise HTTPException(404, "Preview not found.")
    if batch.imported or dt(batch.created_at) + timedelta(hours=1) <= utcnow():
        raise HTTPException(
            409, "Preview was already imported or has expired. Preview again."
        )
    created = []
    for row in batch.rows:
        if row["valid"]:
            fields = CargoCreate.model_validate(row["fields"]).model_dump(mode="json")
            cargo = CargoRequest(
                id=uid("cargo"), organization_id=actor.organization_id, **fields
            )
            db.add(cargo)
            audit(
                db,
                "cargo.created",
                cargo.id,
                actor,
                import_id=batch.id,
                reference=row["reference"],
            )
            created.append(cargo.id)
    if not created:
        raise HTTPException(422, "No valid rows to import.")
    batch.imported = True
    db.commit()
    return {
        "cargo_ids": created,
        "imported_count": len(created),
        "skipped_invalid": sum(not r["valid"] for r in batch.rows),
    }


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
