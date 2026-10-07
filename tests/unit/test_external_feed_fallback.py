import asyncio
import httpx
from datetime import timedelta
from backend.config import settings
from backend.services.timeutils import utcnow
from backend.services.connectors import (
    ExternalTrackingProvider,
    ExternalWeatherProvider,
)


def test_external_position_validates_freshness_before_live_claim(monkeypatch):
    original = httpx.AsyncClient
    payload = {
        "vessel_id": "vessel",
        "latitude": 9.7,
        "longitude": 76.3,
        "speed": 8,
        "heading": 90,
        "timestamp": utcnow().isoformat(),
    }
    monkeypatch.setattr(settings, "tracking_provider", "external")
    monkeypatch.setattr(settings, "tracking_url", "https://example.test/position")
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            ),
            **kwargs,
        ),
    )
    assert not asyncio.run(ExternalTrackingProvider().position("vessel", 9.7, 76.3))[
        "is_demo"
    ]
    payload["timestamp"] = (utcnow() - timedelta(hours=1)).isoformat()
    assert asyncio.run(ExternalTrackingProvider().position("vessel", 9.7, 76.3))[
        "is_demo"
    ]


def test_external_weather_wrong_location_falls_back(monkeypatch):
    original = httpx.AsyncClient
    payload = {
        "location": [10.7, 77.3],
        "rainfall": 12,
        "wind": 20,
        "warning_level": "HIGH",
        "timestamp": utcnow().isoformat(),
    }
    monkeypatch.setattr(settings, "weather_provider", "external")
    monkeypatch.setattr(settings, "weather_url", "https://example.test/weather")
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            ),
            **kwargs,
        ),
    )
    result = asyncio.run(ExternalWeatherProvider().weather(9.7, 76.3))
    assert result["is_demo"] and not result["authoritative_safety_rule"]
