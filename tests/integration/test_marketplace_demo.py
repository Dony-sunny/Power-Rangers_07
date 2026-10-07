from sqlalchemy import select
from backend.models import CargoRequest, CargoVoyage, Vessel, VesselAvailability, ProviderJob, Booking

ADMIN = {"X-Demo-Role": "admin"}
CONTROL = {"X-Demo-Role": "control"}


def test_additive_demo_populates_working_stages_and_preserves_existing_records(client, db):
    existing = client.post("/api/lines/proposals", json={"cargo_ids": ["hero-cargo", "pool-cargo"], "vessel_id": "vembanad"}).json()
    original_cargo = db.get(CargoRequest, "hero-cargo")
    original_ready = original_cargo.ready_time
    counts = {model:len(list(db.scalars(select(model)))) for model in [CargoRequest, Vessel]}
    result = client.post("/api/demo/populate", headers=ADMIN)
    assert result.status_code == 200, result.text
    samples = result.json()["deliveries"]
    assert {item["status"] for item in samples} == {"HELD", "CONFIRMED", "COMPLETED"}
    assert len(list(db.scalars(select(CargoRequest)))) == counts[CargoRequest] + 8
    assert len(list(db.scalars(select(Vessel)))) == counts[Vessel] + 3
    assert db.get(CargoVoyage, existing["id"]).status == "HELD"
    assert db.get(CargoRequest, "hero-cargo").ready_time == original_ready
    visible = client.get("/api/lines", headers=CONTROL).json()
    completed = next(v for v in visible["departures"] if v["id"] == next(s["id"] for s in samples if s["scenario"] == "delivered"))
    assert all(member["receipt"] and member["status"] == "DELIVERED" for member in completed["members"])
    in_transit = next(v for v in visible["departures"] if v["id"] == next(s["id"] for s in samples if s["scenario"] == "transit"))
    assert all(member["status"] == "IN_TRANSIT" for member in in_transit["members"])
    assert visible["impact"]["completed_water_tonnes"] == 138
    before = {model:len(list(db.scalars(select(model)))) for model in [CargoRequest, Vessel, VesselAvailability, CargoVoyage, ProviderJob, Booking]}
    repeated = client.post("/api/demo/populate", headers=ADMIN)
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["deliveries"] == samples
    assert all(len(list(db.scalars(select(model)))) == count for model,count in before.items())


def test_demo_population_requires_demo_admin_and_is_disabled_outside_demo(client, monkeypatch):
    assert client.post("/api/demo/populate").status_code == 403
    from backend.config import settings
    from backend.api.demo import demo_permission
    from fastapi import HTTPException
    from types import SimpleNamespace
    import pytest
    monkeypatch.setattr(settings, "demo_mode", False)
    with pytest.raises(HTTPException) as error:
        demo_permission(SimpleNamespace(role_id="admin"))
    assert error.value.status_code == 403
