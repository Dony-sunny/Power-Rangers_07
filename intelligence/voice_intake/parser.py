import re
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ConfigDict, ValidationError
import httpx
from backend.config import settings
from backend.services.timeutils import IST
from intelligence.document_intake.parser import normalize
from intelligence.provider.llm import provider, ProviderUnavailable
from data.seed.network import PLACES

DEMO_TRANSCRIPT = "Nale 150 ton barge Kochi-ninnu Alappuzha-kku kaali aanu."


class VoiceExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capacity_tonnes: float | None = Field(
        default=None, gt=0, le=5000, allow_inf_nan=False
    )
    origin: str | None = None
    destination: str | None = None
    available_date: str | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    vessel_type: str | None = None


def local_voice(text):
    lower = normalize(text).casefold().replace("നൂറ്റമ്പത്", "150")
    capacity = re.search(r"(\d+(?:\.\d+)?)\s*(?:tonnes?|tons?|t\b)", lower)
    places = "|".join(p.casefold() for p in PLACES)
    origin = re.search(r"(" + places + r")[ -]*(?:ninnu|ninnum)\b", lower)
    destination = re.search(r"(" + places + r")[ -]*(?:kku|k)\b", lower)
    if not origin:
        origin = re.search(r"from\s+([a-z]+)", lower)
    if not destination:
        destination = re.search(r"to\s+([a-z]+)", lower)
    # Native suffixes remain after location normalization.
    if not origin:
        origin = re.search(r"([a-z]+)\s*(?:യിൽ\s*നിന്ന്|യിൽനിന്ന്|നിന്ന്|യിൽ)", lower)
    if not destination:
        destination = re.search(r"([a-z]+)\s*(?:യിലേക്ക്|യിലേയ്ക്ക്|ക്ക്|യിലേക്ക്)", lower)

    def place(match):
        return next(
            (p for p in PLACES if match and p.casefold() == match.group(1)), None
        )

    day = (
        (datetime.now(IST) + timedelta(days=1)).date().isoformat()
        if "nale" in lower or "tomorrow" in lower
        else datetime.now(IST).date().isoformat()
        if "today" in lower
        else None
    )
    return VoiceExtraction(
        capacity_tonnes=float(capacity.group(1)) if capacity else None,
        origin=place(origin),
        destination=place(destination),
        available_date=day,
        vessel_type="BARGE" if "barge" in lower or "ബാർജ്" in lower else None,
    )


async def parse_voice(text, transcription_source="typed_transcript"):
    warnings = []
    source = "local_rules"
    if provider.configured:
        try:
            extraction = VoiceExtraction.model_validate(
                await provider.structured(
                    "Operator transcript. Current local date: "
                    + datetime.now(IST).date().isoformat()
                    + "; timezone Asia/Kolkata.\n"
                    + text,
                    VoiceExtraction.model_json_schema(),
                )
            )
            source = "llm"
        except (ProviderUnavailable, ValidationError):
            warnings.append(
                "AI extraction unavailable; local Malayalam/transliterated parser used."
            )
            extraction = local_voice(text)
    else:
        extraction = local_voice(text)
    fields = extraction.model_dump(mode="json")
    missing = [
        key
        for key in [
            "capacity_tonnes",
            "origin",
            "destination",
            "available_from",
            "available_until",
        ]
        if fields[key] is None
    ]
    if extraction.available_date and not extraction.available_from:
        warnings.append(
            "Only the date was spoken. Confirm exact availability start and end times."
        )
    return {
        "fields": fields,
        "missing_fields": missing,
        "confidence": {k: 0.9 for k, v in fields.items() if v is not None},
        "transcript": text,
        "transcription_source": transcription_source,
        "source": source,
        "is_ai": source == "llm",
        "warnings": warnings,
        "requires_confirmation": True,
    }


async def transcribe(content, filename, mime, use_demo=False):
    if settings.stt_url:
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.post(
                    settings.stt_url,
                    headers={"Authorization": f"Bearer {settings.stt_api_key}"},
                    data={"language": "ml"},
                    files={"file": (filename, content, mime)},
                )
                response.raise_for_status()
                transcript = response.json()["text"]
                if (
                    not isinstance(transcript, str)
                    or not transcript.strip()
                    or len(transcript) > 30000
                ):
                    raise ValueError()
                return transcript, "configured_stt"
        except (httpx.HTTPError, ValueError, KeyError):
            pass
    if settings.demo_mode and use_demo:
        return DEMO_TRANSCRIPT, "demo_transcript_not_audio_transcription"
    raise ProviderUnavailable(
        "Live transcription is unavailable. Type your transcript or explicitly select the demo transcript."
    )
