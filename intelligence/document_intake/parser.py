import re
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from intelligence.provider.llm import provider, ProviderUnavailable
from backend.services.timeutils import IST
from data.seed.network import PLACES


class CargoExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cargo_type: str | None = None
    weight_tonnes: float | None = Field(
        default=None, gt=0, le=10000, allow_inf_nan=False
    )
    volume_m3: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    packaging: str | None = None
    origin: str | None = None
    destination: str | None = None
    ready_time: datetime | None = None
    delivery_deadline: datetime | None = None
    fragile: bool | None = None
    hazardous: bool | None = None
    perishable: bool | None = None
    temperature_control_required: bool | None = None


ALIASES = {
    "കൊച്ചി": "Kochi",
    "കോച്ചി": "Kochi",
    "ആലപ്പുഴ": "Alappuzha",
    "മരട്": "Maradu",
    "വൈക്കം": "Vaikom",
    "തണ്ണീർമുക്കം": "Thanneermukkom",
    "കളമശ്ശേരി": "Kalamassery",
    "സിമന്റ്": "cement",
    "സിമൻറ്": "cement",
    "സ്റ്റീൽ": "steel",
    "കയർ": "coir",
    "അരി": "rice",
    "ടൺ": " ton ",
    "നാളെ": " tomorrow ",
    "ഇന്ന്": " today ",
}
REQUIRED = [
    "cargo_type",
    "weight_tonnes",
    "packaging",
    "origin",
    "destination",
    "ready_time",
    "delivery_deadline",
]


def normalize(text):
    for source, target in ALIASES.items():
        text = text.replace(source, target)
    return text


def explicit_time(text, kind, now):
    pattern = (
        r"(?:ready|pickup|available(?:\s+from)?)\s*(?:time\s*)?[:=]?\s*"
        if kind == "ready"
        else r"(?:deliver(?:y)?(?:\s+by|\s+deadline)?|deadline|\bby)\s*[:=]?\s*"
    )
    match = re.search(
        pattern
        + r"(tomorrow|today|\d{4}-\d{2}-\d{2})(?:[ T,]+)(\d{1,2}):?(\d{2})\s*(am|pm)?",
        text,
        re.I,
    )
    if not match:
        return None
    day, hour, minute, meridiem = match.groups()
    base = (
        now + timedelta(days=1)
        if day.lower() == "tomorrow"
        else now
        if day.lower() == "today"
        else datetime.fromisoformat(day).replace(tzinfo=IST)
    )
    hour = int(hour)
    if meridiem:
        hour = hour % 12 + (12 if meridiem.lower() == "pm" else 0)
    try:
        return base.replace(hour=hour, minute=int(minute), second=0, microsecond=0)
    except ValueError:
        return None


def local_cargo(text, now=None):
    now = now or datetime.now(IST)
    normalized = normalize(text)
    lower = normalized.casefold()
    fields = {}
    for category in ["cement", "steel", "construction", "coir", "rice", "general"]:
        if re.search(r"\b" + category + r"\b", lower):
            fields["cargo_type"] = category
            break
    weight = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:tonnes?|tons?|t\b)", lower)
    kg = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:kg|kilograms?)", lower)
    if weight or kg:
        fields["weight_tonnes"] = (
            float(weight.group(1)) if weight else float(kg.group(1)) / 1000
        )
    volume = re.search(r"(\d+(?:\.\d+)?)\s*(?:m3|m³|cubic\s*met(?:er|re)s?)", lower)
    if volume:
        fields["volume_m3"] = float(volume.group(1))
    for packaging in ["bagged", "bundled", "bales", "pallets", "bulk", "container"]:
        if re.search(r"\b" + packaging + r"\b", lower):
            fields["packaging"] = packaging
            break
    places = "|".join(PLACES)
    origin = re.search(r"(?:from|origin\s*[:=]?)\s*(" + places + r")", normalized, re.I)
    destination = re.search(
        r"(?:to|destination\s*[:=]?)\s*(" + places + r")", normalized, re.I
    )
    for key, match in [("origin", origin), ("destination", destination)]:
        if match:
            fields[key] = next(
                place
                for place in PLACES
                if place.casefold() == match.group(1).casefold()
            )
    fields["ready_time"] = explicit_time(normalized, "ready", now)
    fields["delivery_deadline"] = explicit_time(normalized, "delivery", now)
    for flag in ["fragile", "hazardous", "perishable"]:
        if re.search(r"\b(?:not|non[- ]?)\s*" + flag + r"\b", lower):
            fields[flag] = False
        elif re.search(r"\b" + flag + r"\b", lower):
            fields[flag] = True
    return CargoExtraction.model_validate(fields)


def result(extraction, source, warnings=()):
    fields = extraction.model_dump(mode="json")
    missing = [key for key in REQUIRED if fields.get(key) is None]
    warnings = list(warnings)
    unspecified = [
        key
        for key in [
            "fragile",
            "hazardous",
            "perishable",
            "temperature_control_required",
        ]
        if fields.get(key) is None
    ]
    if unspecified:
        warnings.append(
            "Safety flags not stated in the input: "
            + ", ".join(unspecified)
            + ". Review the unchecked form options; they are not extracted facts."
        )
    for key in ["ready_time", "delivery_deadline"]:
        value = getattr(extraction, key)
        if value and value.tzinfo is None:
            fields[key] = None
            if key not in missing:
                missing.append(key)
            warnings.append(
                f"{key}: timezone is missing; confirm an offset before saving."
            )
    if (
        fields.get("ready_time")
        and fields.get("delivery_deadline")
        and extraction.delivery_deadline <= extraction.ready_time
    ):
        missing.append("valid_delivery_window")
        warnings.append("Delivery deadline must follow cargo readiness.")
    return {
        "fields": fields,
        "confidence": {
            key: 0.95 if source == "local_rules" else 0.80
            for key, value in fields.items()
            if value is not None
        },
        "missing_fields": missing,
        "warnings": warnings,
        "source": source,
        "requires_confirmation": True,
        "is_ai": source == "llm",
        "volume_verified": fields.get("volume_m3") is not None,
    }


async def parse_cargo(text, image_bytes=None, mime=None):
    warnings = []
    if provider.configured:
        try:
            extracted = CargoExtraction.model_validate(
                await provider.structured(
                    "Current local date: "
                    + datetime.now(IST).date().isoformat()
                    + "; timezone Asia/Kolkata. Cargo content:\n"
                    + text,
                    CargoExtraction.model_json_schema(),
                    image_bytes,
                    mime,
                )
            )
            return result(extracted, "llm")
        except (ProviderUnavailable, ValidationError):
            warnings.append(
                "Configured AI provider failed or returned invalid fields; deterministic local extraction used."
            )
    if image_bytes:
        warnings.append(
            "Image understanding needs a configured multimodal provider. No fields were invented."
        )
    try:
        extraction = local_cargo(text)
    except ValidationError:
        extraction = CargoExtraction()
        warnings.append(
            "Text contains values outside the cargo schema. Enter and confirm valid fields manually."
        )
    return result(extraction, "local_rules", warnings)
