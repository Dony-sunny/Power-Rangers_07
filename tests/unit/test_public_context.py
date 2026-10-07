from datetime import datetime, timedelta, timezone
import httpx
import pytest
from backend.services import public_context as service


def payload(now):
    return {"latitude": 9.943, "longitude": 76.326, "utc_offset_seconds": 0,
            "current_units": {"time": "iso8601", "temperature_2m": "°C", "precipitation": "mm", "wind_speed_10m": "km/h", "wind_gusts_10m": "km/h"},
            "current": {"time": now.isoformat(), "temperature_2m": 29, "precipitation": 1.2, "wind_speed_10m": 14, "wind_gusts_10m": 20}}


@pytest.mark.parametrize("defect", ["stale", "future", "units", "nan", "wrong_location", "timezone", "null"])
def test_weather_rejects_unverifiable_models(defect):
    now = datetime.now(timezone.utc)
    item = payload(now)
    if defect == "stale": item["current"]["time"] = (now - timedelta(hours=2)).isoformat()
    if defect == "future": item["current"]["time"] = (now + timedelta(hours=2)).isoformat()
    if defect == "units": item["current_units"]["wind_speed_10m"] = "m/s"
    if defect == "nan": item["current"]["precipitation"] = float("nan")
    if defect == "wrong_location": item["latitude"] = 11
    if defect == "timezone": item["utc_offset_seconds"] = 19800
    if defect == "null": item["current"]["temperature_2m"] = None
    with pytest.raises(ValueError):
        service.validate_weather(item, service.LOCATIONS["maradu"], now)


def test_weather_cache_cooldown_and_offline_state(monkeypatch):
    service._cache.clear()
    service._retry_after.clear()
    calls = []
    class Provider:
        def __init__(self, **kwargs): assert kwargs["timeout"] == 5
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url, params):
            calls.append(url)
            assert url == service.WEATHER_URL
            return httpx.Response(200, json=payload(datetime.now(timezone.utc)), request=httpx.Request("GET", url))
    monkeypatch.setattr(service.httpx, "Client", Provider)
    first = service.weather("maradu")
    assert first["status"] == "CURRENT_MODEL"
    assert service.weather("maradu")["status"] == "CACHED"
    assert len(calls) == 1
    service._cache["maradu"]["tick"] -= 400
    class Offline(Provider):
        def get(self, url, params):
            calls.append(url)
            raise httpx.ConnectError("offline")
    monkeypatch.setattr(service.httpx, "Client", Offline)
    assert service.weather("maradu")["status"] == "CACHED"
    assert "unavailable" in service.weather("maradu")["message"]
    assert len(calls) == 2
    service._cache["maradu"]["model_time"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    result = service.weather("maradu")
    assert result["status"] == "UNAVAILABLE" and result["values"] is None
    assert len(calls) == 2  # Unavailable calls respect the retry cooldown too.
    service._cache.clear()
    service._retry_after.clear()


def test_public_context_is_authenticated_and_rejects_arbitrary_urls(client):
    assert client.get("/api/corridor-context", headers={"X-Demo-Role": "invalid"}).status_code == 403
    assert client.get("/api/corridor-context/weather?location=https://example.com").status_code == 422
    result = client.get("/api/corridor-context").json()
    assert result["source"]["name"] == "Inland Waterways Authority of India"
    assert len(result["locations"]) == 4
