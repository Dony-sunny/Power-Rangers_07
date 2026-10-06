import asyncio
from intelligence.document_intake.parser import local_cargo, result, parse_cargo
from intelligence.voice_intake.parser import local_voice, parse_voice, DEMO_TRANSCRIPT


def test_cargo_parser_schema():
    parsed = local_cargo(
        "80 tonnes cement, bagged, 60 m3, from Kalamassery to Alappuzha. Ready tomorrow 08:00; deliver by tomorrow 22:00."
    )
    assert parsed.weight_tonnes == 80 and parsed.volume_m3 == 60
    assert parsed.origin == "Kalamassery" and parsed.destination == "Alappuzha"
    assert result(parsed, "local_rules")["missing_fields"] == []


def test_missing_fields_are_never_invented():
    parsed = asyncio.run(parse_cargo("cement from Kochi to Alappuzha"))
    assert parsed["fields"]["weight_tonnes"] is None
    assert {"weight_tonnes", "packaging", "ready_time", "delivery_deadline"} <= set(
        parsed["missing_fields"]
    )
    assert not parsed["is_ai"]


def test_voice_schema_and_missing_window():
    parsed = local_voice(DEMO_TRANSCRIPT)
    assert (
        parsed.capacity_tonnes == 150
        and parsed.origin == "Kochi"
        and parsed.destination == "Alappuzha"
    )
    result = asyncio.run(parse_voice(DEMO_TRANSCRIPT))
    assert (
        "available_until" in result["missing_fields"]
        and result["requires_confirmation"]
    )


def test_native_malayalam_voice():
    parsed = local_voice("നാളെ 150 ടൺ ബാർജ് കൊച്ചിയിൽനിന്ന് ആലപ്പുഴയിലേക്ക് ഒഴിവാണ്")
    assert (
        parsed.capacity_tonnes == 150
        and parsed.origin == "Kochi"
        and parsed.destination == "Alappuzha"
    )


def test_negative_text_weight_is_not_silently_made_positive():
    parsed = asyncio.run(parse_cargo("-80 tonnes cement from Kochi to Alappuzha"))
    assert parsed["fields"]["weight_tonnes"] is None
    assert "weight_tonnes" in parsed["missing_fields"]
