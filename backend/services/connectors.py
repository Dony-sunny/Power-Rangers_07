"""Optional validated provider contracts. Demo and no-op states are explicit."""

from typing import Protocol, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ConfigDict, model_validator
import httpx
from backend.config import settings
from backend.services.timeutils import utcnow


class Position(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vessel_id: str
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    speed: float = Field(ge=0, le=100, allow_inf_nan=False)
    heading: float = Field(ge=0, lt=360, allow_inf_nan=False)
    timestamp: datetime

    @model_validator(mode="after")
    def timestamp_zone(self):
        if not self.timestamp.tzinfo:
            raise ValueError("Position timestamp needs timezone")
        return self


class Weather(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: tuple[float, float]
    rainfall: float = Field(ge=0, le=2000, allow_inf_nan=False)
    wind: float = Field(ge=0, le=500, allow_inf_nan=False)
    warning_level: Literal["NONE", "ADVISORY", "HIGH", "SEVERE"]
    timestamp: datetime

    @model_validator(mode="after")
    def location_zone(self):
        if not self.timestamp.tzinfo or not (
            -90 <= self.location[0] <= 90 and -180 <= self.location[1] <= 180
        ):
            raise ValueError("Weather requires coordinates and timezone")
        return self


class TrackingProvider(Protocol):
    async def position(self, vessel_id: str, latitude: float, longitude: float): ...


class WeatherProvider(Protocol):
    async def weather(self, latitude: float, longitude: float): ...


class DemoTrackingProvider:
    async def position(self, vessel_id, latitude, longitude):
        return {
            "position": Position(
                vessel_id=vessel_id,
                latitude=latitude,
                longitude=longitude,
                speed=0,
                heading=0,
                timestamp=utcnow(),
            ).model_dump(mode="json"),
            "source": "SIMULATED milestone position",
            "is_demo": True,
        }


class ExternalTrackingProvider:
    async def position(self, vessel_id, latitude, longitude):
        if settings.tracking_provider != "demo" and settings.tracking_url:
            try:
                async with httpx.AsyncClient(
                    timeout=settings.provider_timeout_seconds
                ) as client:
                    response = await client.get(
                        settings.tracking_url,
                        params={"vessel_id": vessel_id},
                        headers={
                            "Authorization": f"Bearer {settings.tracking_api_key}"
                        },
                    )
                    response.raise_for_status()
                    position = Position.model_validate(response.json())
                    if (
                        position.vessel_id != vessel_id
                        or abs((utcnow() - position.timestamp).total_seconds()) > 900
                    ):
                        raise ValueError()
                    return {
                        "position": position.model_dump(mode="json"),
                        "source": "Configured external tracking provider; not an asserted AIS integration",
                        "is_demo": False,
                    }
            except (httpx.HTTPError, ValueError, TypeError):
                pass
        result = await DemoTrackingProvider().position(vessel_id, latitude, longitude)
        result["warning"] = (
            "External tracking unavailable/unconfigured/stale; demo fallback selected."
        )
        return result


class DemoWeatherProvider:
    async def weather(self, latitude, longitude):
        return {
            "weather": Weather(
                location=(latitude, longitude),
                rainfall=0,
                wind=8,
                warning_level="NONE",
                timestamp=utcnow(),
            ).model_dump(mode="json"),
            "source": "SIMULATED weather fixture · not IMD",
            "is_demo": True,
            "authoritative_safety_rule": False,
        }


class ExternalWeatherProvider:
    async def weather(self, latitude, longitude):
        if settings.weather_provider != "demo" and settings.weather_url:
            try:
                async with httpx.AsyncClient(
                    timeout=settings.provider_timeout_seconds
                ) as client:
                    response = await client.get(
                        settings.weather_url,
                        params={"latitude": latitude, "longitude": longitude},
                        headers={"Authorization": f"Bearer {settings.weather_api_key}"},
                    )
                    response.raise_for_status()
                    weather = Weather.model_validate(response.json())
                    if (
                        abs((utcnow() - weather.timestamp).total_seconds()) > 3600
                        or abs(weather.location[0] - latitude) > 0.1
                        or abs(weather.location[1] - longitude) > 0.1
                    ):
                        raise ValueError()
                    return {
                        "weather": weather.model_dump(mode="json"),
                        "source": "Configured external weather provider · not an asserted IMD integration",
                        "is_demo": False,
                        "authoritative_safety_rule": False,
                    }
            except (httpx.HTTPError, ValueError, TypeError):
                pass
        result = await DemoWeatherProvider().weather(latitude, longitude)
        result["warning"] = (
            "External weather unavailable/unconfigured/stale; demo fallback selected."
        )
        return result


class PaymentProvider(Protocol):
    def create_payment(self, reference: str, amount: float): ...
    def get_status(self, reference: str): ...
    def refund(self, reference: str): ...


class DemoPaymentProvider:
    def create_payment(self, reference, amount):
        return {
            "reference": reference,
            "amount": amount,
            "status": "PENDING",
            "prototype": True,
            "funds_moved": False,
        }

    def get_status(self, reference):
        return {"reference": reference, "status": "NOT_CONNECTED", "prototype": True}

    def refund(self, reference):
        return {"reference": reference, "status": "NOT_CONNECTED", "funds_moved": False}


class InsuranceProvider(Protocol):
    def request_quote(self, payload: dict): ...
    def attach_policy(self, payload: dict): ...
    def get_policy_status(self, reference: str): ...


class NoOpInsuranceProvider:
    def request_quote(self, payload):
        return {"status": "NOT_CONNECTED", "prototype": True}

    def attach_policy(self, payload):
        return {"status": "NOT_CONNECTED", "attached": False}

    def get_policy_status(self, reference):
        return {"status": "NOT_CONNECTED", "reference": reference}


class GovernmentDocumentProvider(Protocol):
    def prepare_payload(self, payload: dict): ...
    def submit(self, payload: dict): ...
    def get_status(self, reference: str): ...


class NoOpGovernmentProvider:
    def prepare_payload(self, payload):
        return {
            "payload": payload,
            "status": "PROTOTYPE_READY_DATA",
            "issued_document": False,
        }

    def submit(self, payload):
        return {"status": "NOT_CONNECTED", "submitted": False}

    def get_status(self, reference):
        return {"status": "NOT_CONNECTED", "reference": reference}


class IdentityProvider(Protocol):
    """Implementations verify issuer/audience/signature/expiry before DB role resolution."""

    def verify_token(self, token: str) -> dict: ...


def connector_status():
    return {
        "tracking": {
            "configured": settings.tracking_provider != "demo"
            and bool(settings.tracking_url),
            "default": "SIMULATED",
        },
        "weather": {
            "configured": settings.weather_provider != "demo"
            and bool(settings.weather_url),
            "default": "SIMULATED",
            "authoritative_safety_rule": False,
        },
        "payment": "Prototype / Not connected",
        "insurance": "Prototype / Not connected",
        "government": "Prototype / Not connected",
        "identity": "Signed stored identities; OIDC/enterprise SSO not connected",
    }
