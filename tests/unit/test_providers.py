import asyncio
import httpx
import pytest
from backend.config import settings
from intelligence.provider.llm import provider, speech_provider, ProviderUnavailable
from intelligence.document_intake.parser import parse_cargo
from intelligence.voice_intake.parser import local_voice, transcribe


def mock_http(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    monkeypatch.setattr(settings, "ai_provider", "chat_completions")
    monkeypatch.setattr(settings, "llm_api_key", "test-only-not-a-credential")
    monkeypatch.setattr(settings, "llm_model", "mock")


@pytest.mark.parametrize(
    "content",
    [
        '{"cargo_type":"cement","weight_tonnes":80}',
        "not json",
        '{"weight_tonnes":-1}',
        '{"cargo_type":"cement","invented_field":1}',
    ],
)
def test_llm_outputs_validated_and_failure_fallback(monkeypatch, content):
    mock_http(
        monkeypatch,
        lambda request: httpx.Response(
            200, json={"choices": [{"message": {"content": content}}]}
        ),
    )
    result = asyncio.run(parse_cargo("80 tonnes cement"))
    assert result["fields"]["weight_tonnes"] == 80
    assert result["requires_confirmation"]
    assert "origin" in result["missing_fields"]
    assert result["source"] == (
        "llm" if content.startswith('{"cargo_type":"cement","weight') else "local_rules"
    )


def test_retry_only_transient_and_timeout_fallback(monkeypatch):
    calls = []

    def unavailable(request):
        calls.append(request)
        return httpx.Response(503)

    mock_http(monkeypatch, unavailable)
    assert asyncio.run(parse_cargo("80 tonnes cement"))["source"] == "local_rules"
    assert len(calls) == 2


def test_speech_live_and_explicit_demo(monkeypatch):
    mock_http(
        monkeypatch,
        lambda request: httpx.Response(
            200, json={"text": "Tomorrow 120 ton capacity undu Kochi to Alappuzha."}
        ),
    )
    monkeypatch.setattr(settings, "stt_url", "https://stt.example.test")
    text, source = asyncio.run(transcribe(b"audio", "voice.wav", "audio/wav"))
    assert source == "configured_stt"
    assert local_voice(text).capacity_tonnes == 120
    monkeypatch.setattr(settings, "stt_url", "")
    with pytest.raises(ProviderUnavailable):
        asyncio.run(transcribe(b"audio", "voice.wav", "audio/wav"))
    assert (
        "not_audio_transcription"
        in asyncio.run(transcribe(b"audio", "voice.wav", "audio/wav", True))[1]
    )


@pytest.mark.parametrize(
    "text,tonnes",
    [
        ("Ente 150 tonne barge nale Kochiyil free aanu, Alappuzha side pokam.", 150),
        ("Tomorrow 120 ton capacity undu Kochi to Alappuzha.", 120),
        ("Nale Kochi-ninnu Alappuzha-kku 150 ton barge kaali aanu", 150),
    ],
)
def test_malayalam_variations(text, tonnes):
    extraction = local_voice(text)
    assert extraction.capacity_tonnes == tonnes
    assert extraction.origin == "Kochi"
    assert extraction.destination == "Alappuzha"
    assert extraction.available_from is None


def test_uncertain_destination_not_invented():
    assert (
        local_voice("Tomorrow 120 ton capacity Kochiyil free aanu.").destination is None
    )
