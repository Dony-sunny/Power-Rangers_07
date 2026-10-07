import asyncio
from backend.services.connectors import (
    ExternalTrackingProvider,
    ExternalWeatherProvider,
    NoOpInsuranceProvider,
    NoOpGovernmentProvider,
    DemoPaymentProvider,
)


def test_optional_tracking_weather_default_fallbacks():
    position = asyncio.run(ExternalTrackingProvider().position("vessel", 9.7, 76.3))
    assert position["is_demo"] and position["position"]["vessel_id"] == "vessel"
    weather = asyncio.run(ExternalWeatherProvider().weather(9.7, 76.3))
    assert weather["is_demo"] and not weather["authoritative_safety_rule"]


def test_commercial_noop_providers_never_fabricate_success():
    assert NoOpInsuranceProvider().attach_policy({})["attached"] is False
    assert NoOpGovernmentProvider().submit({})["submitted"] is False
    assert (
        DemoPaymentProvider().create_payment("reference", 100)["funds_moved"] is False
    )
