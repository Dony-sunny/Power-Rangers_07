"""Read-only public context. It never supplies navigability or booking constraints."""
import math
import threading
import time
from datetime import datetime, timezone

import httpx

IWAI_URL = "https://www.iwai.gov.in/offerings/national-waterway/national-waterways3"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
LOCATIONS = {
    "maradu": {"name": "Maradu / Kochi", "latitude": 9.943, "longitude": 76.326},
    "vaikom": {"name": "Vaikom", "latitude": 9.748, "longitude": 76.397},
    "thanneermukkom": {"name": "Thanneermukkom", "latitude": 9.669, "longitude": 76.387},
    "alappuzha": {"name": "Alappuzha", "latitude": 9.498, "longitude": 76.338},
}
_cache = {}
_retry_after = {}
_locks = {key: threading.Lock() for key in LOCATIONS}
TTL_SECONDS = 300
MAX_AGE_SECONDS = 5400


def corridor_context():
    return {
        "title": "National Waterway 3 reference",
        "description": "IWAI describes the Kottapuram–Kollam West Coast Canal (168 km), Udyogmandal Canal (23 km) and Champakara Canal (14 km). These describe the original canal system; this is not a claim about the full extended statutory length.",
        "terminals": ["Maradu", "Vaikom", "Thanneermukkom", "Alappuzha"],
        "source": {"name": "Inland Waterways Authority of India", "url": IWAI_URL, "checked_on": "2026-10-07"},
        "limitations": "Published corridor information does not establish current channel depth, terminal availability, flood restrictions or clearance to navigate. Booking feasibility still uses clearly labeled prototype fixtures.",
        "locations": [{"id": key, **value} for key, value in LOCATIONS.items()],
    }


def validate_weather(payload, location, now):
    """Reject wrong units, bad locations, stale models and unbounded numbers."""
    expected = {"temperature_2m": "°C", "precipitation": "mm", "wind_speed_10m": "km/h", "wind_gusts_10m": "km/h", "time": "iso8601"}
    if any(payload["current_units"].get(key) != unit for key, unit in expected.items()):
        raise ValueError("Unexpected units")
    if payload.get("utc_offset_seconds") != 0:
        raise ValueError("Unexpected time zone")
    for key in ["latitude", "longitude"]:
        value = payload[key]
        if isinstance(value, bool) or not math.isfinite(float(value)) or abs(float(value) - location[key]) > .3:
            raise ValueError("Unexpected model location")
    current = payload["current"]
    observed = datetime.fromisoformat(current["time"])
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    age = now.timestamp() - observed.timestamp()
    if age < -900 or age > MAX_AGE_SECONDS:
        raise ValueError("Model time outside freshness window")
    ranges = {"temperature_2m": (-80, 65), "precipitation": (0, 500), "wind_speed_10m": (0, 400), "wind_gusts_10m": (0, 500)}
    values = {}
    for key, (lower, upper) in ranges.items():
        value = current[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError("Invalid weather value")
        values[key] = value
    return {"model_time": observed.isoformat(), "values": values, "units": expected}


def weather(location_id):
    location = LOCATIONS[location_id]
    base = {"location": {"id": location_id, **location}, "source": {"name": "Open-Meteo", "url": "https://open-meteo.com/", "documentation": "https://open-meteo.com/en/docs", "license": "CC BY 4.0; free API for this non-commercial prototype"},
            "limitations": "Weather model output, not a station observation, navigation advisory or live waterway clearance. This information does not change route feasibility or dispatch decisions."}
    # One in-flight request per allowed location, with failure cooldown and no arbitrary URL input.
    with _locks[location_id]:
        now = datetime.now(timezone.utc)
        tick = time.monotonic()
        cached = _cache.get(location_id)
        valid_cache = cached and now.timestamp() - datetime.fromisoformat(cached["model_time"]).timestamp() <= MAX_AGE_SECONDS
        if valid_cache and tick - cached["tick"] < TTL_SECONDS:
            return {**base, **{key: value for key, value in cached.items() if key != "tick"}, "status": "CACHED", "message": "Validated model cached for up to five minutes."}
        if tick >= _retry_after.get(location_id, 0):
            try:
                with httpx.Client(timeout=5.0, follow_redirects=False, trust_env=False) as client:
                    response = client.get(WEATHER_URL, params={"latitude": location["latitude"], "longitude": location["longitude"], "current": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m", "timezone": "GMT", "wind_speed_unit": "kmh", "forecast_days": 1})
                    response.raise_for_status()
                    if len(response.content) > 65536:
                        raise ValueError("Oversized weather response")
                    snapshot = validate_weather(response.json(), location, now)
                snapshot.update({"fetched_at": datetime.now(timezone.utc).isoformat(), "tick": tick})
                _cache[location_id] = snapshot
                _retry_after.pop(location_id, None)
                return {**base, **{key: value for key, value in snapshot.items() if key != "tick"}, "status": "CURRENT_MODEL", "message": "Validated current model retrieved from Open-Meteo."}
            except (httpx.HTTPError, ValueError, KeyError, TypeError, OverflowError):
                _retry_after[location_id] = tick + 60
        if valid_cache:
            return {**base, **{key: value for key, value in cached.items() if key != "tick"}, "status": "CACHED", "message": "Provider unavailable. Showing the last validated model; check its timestamp."}
        return {**base, "status": "UNAVAILABLE", "values": None, "model_time": None, "fetched_at": None, "message": "Weather could not be verified. Retry after one minute. No synthetic weather has been substituted."}
