from io import BytesIO
from pathlib import Path
import csv
from fastapi import HTTPException
from pypdf import PdfReader

MAX_UPLOAD = 8 * 1024 * 1024


async def read_upload(upload):
    content = await upload.read(MAX_UPLOAD + 1)
    if not content or len(content) > MAX_UPLOAD:
        raise HTTPException(413, "Upload must contain data and be at most 8 MB.")
    filename = Path((upload.filename or "upload").replace("\\", "/")).name
    suffix = Path(filename).suffix.lower()
    return content, filename, suffix


def document_text(content, suffix):
    if suffix in {".txt", ".csv"}:
        try:
            return content.decode("utf-8-sig")[:30000]
        except UnicodeDecodeError:
            raise HTTPException(422, "Text documents must use UTF-8.") from None
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(415, "File is not a valid PDF.")
        try:
            import subprocess, sys, json

            completed = subprocess.run(
                [sys.executable, "-m", "intelligence.document_intake.pdf_worker"],
                input=content,
                capture_output=True,
                timeout=12,
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            )
            if completed.returncode != 0:
                raise ValueError()
            return json.loads(completed.stdout)["text"]
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                422, "PDF could not be safely read. Use a text-based, unencrypted PDF."
            ) from None
    raise HTTPException(
        415,
        "Supported uploads: text-based PDF, UTF-8 TXT/CSV, PNG or JPEG with a configured multimodal provider.",
    )


def csv_preview(content):
    try:
        rows = list(csv.DictReader(content.decode("utf-8-sig").splitlines()))
    except (UnicodeDecodeError, csv.Error):
        raise HTTPException(422, "CSV must be UTF-8 with a header row.") from None
    if len(rows) > 200:
        raise HTTPException(413, "Bulk preview limit: 200 cargo rows.")
    return rows
