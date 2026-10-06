from datetime import timedelta
from data.seed.network import tomorrow


def test_manual_vertical_slice(client):
    start = tomorrow()
    payload = {
        "cargo_type": "cement",
        "weight_tonnes": 80,
        "volume_m3": 60,
        "packaging": "bagged",
        "origin": "Kalamassery",
        "destination": "Alappuzha",
        "ready_time": start.isoformat(),
        "delivery_deadline": (start + timedelta(hours=14)).isoformat(),
        "last_mile_required": False,
    }
    response = client.post("/api/cargo", json=payload)
    assert response.status_code == 201, response.text
    cargo = response.json()
    matches = client.get(f"/api/cargo/{cargo['id']}/matches").json()
    assert matches["recommendations"][0]["vessel_id"] == "vembanad"
    deep = next(v for v in matches["rejected"] if v["vessel_id"] == "deep-blue")
    assert any("draft" in reason for reason in deep["feasibility"]["reasons"])
    comparison = client.get(
        f"/api/cargo/{cargo['id']}/compare?vessel_id=vembanad"
    ).json()
    assert len(comparison["plans"]) == 3
    response = client.post(
        "/api/bookings",
        json={
            "cargo_id": cargo["id"],
            "vessel_id": "vembanad",
            "mode": "HYBRID",
            "approved": True,
        },
    )
    assert response.status_code == 201, response.text
    shipment = response.json()["shipment"]
    assert (
        client.get(f"/api/shipments/{shipment['id']}").json()["events"][0]["status"]
        == "CONFIRMED"
    )
    for state in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING", "DELIVERED"]:
        response = client.post(
            f"/api/shipments/{shipment['id']}/transition",
            json={"status": state},
            headers={"X-Demo-Role": "dispatch"},
        )
        assert response.status_code == 200, response.text
    assert response.json()["progress"] == 1


def test_booking_requires_explicit_approval(client):
    assert (
        client.post(
            "/api/bookings", json={"cargo_id": "hero-cargo", "vessel_id": "vembanad"}
        ).status_code
        == 422
    )


def test_tenant_boundary(client):
    assert client.get("/api/cargo/unserved-cargo/matches").status_code == 404
    assert (
        client.get(
            "/api/cargo/hero-cargo/matches", headers={"X-Demo-User": "competitor-user"}
        ).status_code
        == 404
    )
