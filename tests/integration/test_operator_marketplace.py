from copy import deepcopy
from sqlalchemy import select
from backend.models import CargoVoyage, VesselAvailability, Vessel, VesselCertificate
from backend.repositories.common import record

OPERATOR = {"X-Demo-Role": "operator"}
OTHER_OPERATOR = {"X-Demo-Role": "operator", "X-Demo-User": "demo-pamba-operator"}


def sample_listing(db):
    return db.scalar(select(VesselAvailability).where(VesselAvailability.vessel_id == "vembanad", VesselAvailability.destination == "Alappuzha"))


def payload(listing, **changes):
    value = record(listing)
    return {**{key: value[key] for key in ["vessel_id", "origin", "destination", "available_from", "available_until", "capacity_tonnes", "volume_m3"]}, **changes}


def test_operator_edits_existing_listing_without_creating_a_duplicate(client, db):
    listing = sample_listing(db)
    count = len(list(db.scalars(select(VesselAvailability))))
    response = client.put(f"/api/availability/{listing.id}", headers=OPERATOR, json=payload(listing, capacity_tonnes=120, volume_m3=180))
    assert response.status_code == 200, response.text
    assert response.json()["id"] == listing.id
    assert response.json()["capacity_tonnes"] == 120
    assert len(list(db.scalars(select(VesselAvailability)))) == count
    assert db.get(VesselAvailability, listing.id).volume_m3 == 180
    response = client.put(f"/api/availability/{listing.id}", headers=OPERATOR, json=payload(listing, capacity_tonnes=999))
    assert response.status_code == 422
    assert db.get(VesselAvailability, listing.id).capacity_tonnes == 120


def test_only_listing_owner_can_edit_or_change_visibility(client, db):
    listing = sample_listing(db)
    assert client.put(f"/api/availability/{listing.id}", headers=OTHER_OPERATOR, json=payload(listing)).status_code == 404
    assert client.post(f"/api/availability/{listing.id}/visibility?active=false", headers=OTHER_OPERATOR).status_code == 404
    assert client.put(f"/api/availability/{listing.id}", json=payload(listing)).status_code == 403
    assert listing.active


def test_pause_and_republish_affect_matching(client, db):
    listing = sample_listing(db)
    assert client.post(f"/api/availability/{listing.id}/visibility?active=false", headers=OPERATOR).status_code == 200
    matched = client.get("/api/cargo/hero-cargo/matches").json()
    assert all(m["vessel_id"] != "vembanad" for m in matched["recommendations"])
    assert client.post(f"/api/availability/{listing.id}/visibility?active=true", headers=OPERATOR).status_code == 200
    matched = client.get("/api/cargo/hero-cargo/matches").json()
    assert any(m["vessel_id"] == "vembanad" for m in matched["recommendations"])


def test_reserved_window_cannot_be_edited_or_paused(client, db):
    listing = sample_listing(db)
    response = client.post("/api/lines/proposals", json={"cargo_ids": ["hero-cargo", "pool-cargo"], "vessel_id": "vembanad", "availability_id": listing.id})
    assert response.status_code == 201, response.text
    original = payload(listing)
    for result in [
        client.put(f"/api/availability/{listing.id}", headers=OPERATOR, json={**original, "capacity_tonnes": 120}),
        client.post(f"/api/availability/{listing.id}/visibility?active=false", headers=OPERATOR),
    ]:
        assert result.status_code == 409, result.text
        assert "reserved" in result.json()["detail"]
    assert listing.active
    assert payload(listing) == original
    assert db.get(CargoVoyage, response.json()["id"]).status == "HELD"


def new_boat_payload(db, demo_review=False):
    listing = sample_listing(db)
    return {
        "vessel": {
            "name": "New operator boat", "max_capacity_tonnes": 100,
            "max_volume_m3": 160, "length": 38, "beam": 7.5,
            "loaded_draft": 1.3, "air_draft": 3.8,
            "current_location": "Maradu", "cargo_categories": ["cement"],
            "rate_per_tonne_km": 3,
        },
        "availability": {key: value for key, value in payload(listing, capacity_tonnes=100, volume_m3=160).items() if key != "vessel_id"},
        "demo_certificate_review": demo_review,
    }


def test_new_boat_and_first_listing_are_saved_for_the_actual_operator(client, db):
    body = new_boat_payload(db, demo_review=True)
    result = client.post("/api/vessels/with-availability", headers=OTHER_OPERATOR, json=body)
    assert result.status_code == 201, result.text
    saved = result.json()
    boat = db.get(Vessel, saved["vessel"]["id"])
    assert boat.organization_id == db.get(Vessel, "pamba").organization_id
    assert saved["availability"]["vessel_id"] == boat.id
    assert saved["certificate_source"] == "SIMULATED"
    assert boat.compliance_status == "PASS"
    certificates = list(db.scalars(select(VesselCertificate).where(VesselCertificate.vessel_id == boat.id)))
    assert {c.kind for c in certificates} == {"REGISTRATION", "INSURANCE"}
    assert all(c.verified for c in certificates)
    matches = client.get("/api/cargo/hero-cargo/matches").json()
    assert any(m["vessel_id"] == boat.id for m in matches["recommendations"])
    assert client.put(f"/api/availability/{saved['availability']['id']}", headers=OPERATOR, json={**body["availability"], "vessel_id": boat.id}).status_code == 404


def test_new_boat_validation_leaves_no_partial_listing_and_no_unverified_booking(client, db):
    body = new_boat_payload(db)
    boats = len(list(db.scalars(select(Vessel))))
    windows = len(list(db.scalars(select(VesselAvailability))))
    invalid = deepcopy(body)
    invalid["availability"]["capacity_tonnes"] = 101
    assert client.post("/api/vessels/with-availability", headers=OPERATOR, json=invalid).status_code == 422
    assert client.post("/api/vessels/with-availability", json=body).status_code == 403
    assert len(list(db.scalars(select(Vessel)))) == boats
    assert len(list(db.scalars(select(VesselAvailability)))) == windows
    result = client.post("/api/vessels/with-availability", headers=OPERATOR, json=body)
    assert result.status_code == 201, result.text
    saved = result.json()
    assert saved["vessel"]["compliance_status"] == "PENDING"
    assert saved["certificate_source"] == "PENDING_REVIEW"
    matches = client.get("/api/cargo/hero-cargo/matches").json()
    assert all(m["vessel_id"] != saved["vessel"]["id"] for m in matches["recommendations"])


def test_simulated_boat_certificates_are_unavailable_outside_demo(client, db, monkeypatch):
    from backend.config import settings
    from backend.models import User
    from backend.api.routes import register_boat_listing
    from backend.schemas.requests import VesselListing
    from fastapi import HTTPException
    import pytest
    monkeypatch.setattr(settings, "demo_mode", False)
    # Test the boundary with an already authenticated operator; demo headers are
    # themselves disabled when demo mode is off.
    actor = db.get(User, "demo-operator")
    with pytest.raises(HTTPException) as error:
        register_boat_listing(VesselListing.model_validate(new_boat_payload(db, True)), db, actor)
    assert error.value.status_code == 403
