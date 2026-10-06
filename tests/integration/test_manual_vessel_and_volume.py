from datetime import timedelta
from data.seed.network import tomorrow


def test_manual_vessel_requires_certificates_then_matches(client):
    operator = {"X-Demo-Role": "operator"}
    start = tomorrow()
    response = client.post(
        "/api/vessels",
        headers=operator,
        json={
            "name": "MV Test Pilot",
            "max_capacity_tonnes": 150,
            "max_volume_m3": 220,
            "length": 38,
            "beam": 7,
            "loaded_draft": 1.5,
            "air_draft": 4,
            "current_location": "Maradu",
            "cargo_categories": ["cement", "steel"],
        },
    )
    assert response.status_code == 201, response.text
    vessel = response.json()
    availability = {
        "vessel_id": vessel["id"],
        "origin": "Maradu",
        "destination": "Alappuzha",
        "available_from": start.isoformat(),
        "available_until": (start + timedelta(days=2)).isoformat(),
        "capacity_tonnes": 150,
        "volume_m3": 220,
    }
    assert (
        client.post(
            "/api/availability", headers=operator, json=availability
        ).status_code
        == 201
    )
    assert vessel["id"] not in {
        m["vessel_id"]
        for m in client.get("/api/cargo/hero-cargo/matches").json()["recommendations"]
    }
    for kind in ["REGISTRATION", "INSURANCE"]:
        result = client.post(
            f"/api/vessels/{vessel['id']}/certificates",
            headers={"X-Demo-Role": "compliance"},
            json={
                "kind": kind,
                "expires_at": (start + timedelta(days=180)).isoformat(),
                "verified": True,
            },
        )
        assert result.status_code == 200, result.text
    assert vessel["id"] in {
        m["vessel_id"]
        for m in client.get("/api/cargo/hero-cargo/matches").json()["recommendations"]
    }


def test_missing_volume_can_be_verified_before_departure(client, db):
    from backend.models import CargoRequest

    db.get(CargoRequest, "hero-cargo").volume_m3 = None
    db.commit()
    booking = client.post(
        "/api/bookings",
        json={
            "cargo_id": "hero-cargo",
            "vessel_id": "vembanad",
            "mode": "HYBRID",
            "approved": True,
        },
    ).json()
    shipment_id = booking["shipment"]["id"]
    for status in ["SCHEDULED", "LOADING"]:
        assert (
            client.post(
                f"/api/shipments/{shipment_id}/transition",
                headers={"X-Demo-Role": "dispatch"},
                json={"status": status},
            ).status_code
            == 200
        )
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/transition",
            headers={"X-Demo-Role": "captain"},
            json={"status": "IN_TRANSIT"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/operations",
            headers={"X-Demo-Role": "warehouse"},
            json={"actual_volume_m3": 300},
        ).status_code
        == 409
    )
    result = client.post(
        f"/api/shipments/{shipment_id}/operations",
        headers={"X-Demo-Role": "warehouse"},
        json={"actual_volume_m3": 60, "packing_ready": True},
    )
    assert result.status_code == 200, result.text
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/transition",
            headers={"X-Demo-Role": "captain"},
            json={"status": "IN_TRANSIT"},
        ).status_code
        == 200
    )


def test_text_pdf_extracts_without_model(client):
    from scripts.make_demo_documents import text_pdf

    pdf = text_pdf(
        [
            "SYNTHETIC PURCHASE ORDER",
            "80 tonnes cement, bagged, volume 60 m3.",
            "From Kalamassery to Alappuzha.",
            "Ready tomorrow 08:00; deliver by tomorrow 22:00.",
        ]
    )
    result = client.post(
        "/api/intake/cargo/document",
        files={"file": ("purchase_order.pdf", pdf, "application/pdf")},
    )
    assert result.status_code == 200, result.text
    assert (
        result.json()["fields"]["weight_tonnes"] == 80
        and result.json()["missing_fields"] == []
    )


def test_empty_impact_has_no_invented_savings(client):
    impact = client.get("/api/impact", headers={"X-Demo-Role": "government"}).json()
    assert (
        impact["tonnes_shifted"] == 0
        and impact["co2_avoided_kg"] == 0
        and impact["cost_savings"] == 0
    )
