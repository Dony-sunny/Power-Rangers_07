import json
import subprocess
import sys
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException


def validate_image(content):
    try:
        with Image.open(BytesIO(content)) as image:
            if (
                image.format not in {"PNG", "JPEG"}
                or image.width * image.height > 12_000_000
            ):
                raise ValueError()
            image.verify()
        with Image.open(BytesIO(content)) as image:
            return image.convert("RGB")
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError):
        raise HTTPException(
            415, "Use a valid PNG/JPEG image of at most 12 megapixels."
        ) from None


def run_ocr(content, suffix):
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "intelligence.document_intake.ocr_worker", suffix],
            input=content,
            capture_output=True,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if completed.returncode != 0:
            raise ValueError()
        result = json.loads(completed.stdout)
        if not isinstance(result.get("text"), str):
            raise ValueError()
        return result
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return {
            "text": "",
            "source": "ocr_unavailable",
            "warnings": [
                "Local OCR timed out or is unavailable. Review missing fields manually or configure an image-capable provider."
            ],
            "confidence": None,
        }
