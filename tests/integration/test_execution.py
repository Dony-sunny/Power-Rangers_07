def book(client):
    response = client.post(
        "/api/bookings",
        json={
            "cargo_id": "hero-cargo",
            "vessel_id": "vembanad",
            "mode": "HYBRID",
            "approved": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_pool_booking_reserves_each_load_and_impact_is_derived(client):
    pool = client.post("/api/cargo/hero-cargo/pool?vessel_id=vembanad").json()
    response = client.post(
        "/api/bookings",
        json={
            "cargo_id": "hero-cargo",
            "vessel_id": "vembanad",
            "mode": "HYBRID",
            "pool_id": pool["pool"]["id"],
            "approved": True,
        },
    )
    assert response.status_code == 201, response.text
    assert len(response.json()["bookings"]) == 2
    metrics = client.get("/api/impact", headers={"X-Demo-Role": "government"}).json()
    assert metrics["tonnes_shifted"] == 138 and metrics["utilization_after_pct"] == 92
    assert metrics["completed_tonnes_shifted"] == 0
    assert (
        client.get("/api/impact", headers={"X-Demo-Role": "warehouse"}).status_code
        == 403
    )


def test_cancellation_returns_alternatives_and_requires_approval(client):
    result = book(client)
    booking_id = result["booking"]["id"]
    response = client.post(
        f"/api/bookings/{booking_id}/disrupt",
        headers={"X-Demo-Role": "dispatch"},
        json={"kind": "VESSEL_UNAVAILABLE"},
    )
    assert response.status_code == 200, response.text
    assert any(a["vessel_id"] == "pamba" for a in response.json()["alternatives"])
    assert (
        client.post(
            f"/api/bookings/{booking_id}/recover",
            headers={"X-Demo-Role": "dispatch"},
            json={"vessel_id": "pamba"},
        ).status_code
        == 422
    )
    approved = client.post(
        f"/api/bookings/{booking_id}/recover",
        headers={"X-Demo-Role": "dispatch"},
        json={"vessel_id": "pamba", "mode": "HYBRID", "approved": True},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["booking"]["vessel_id"] == "pamba"


def test_invalid_state_and_duplicate_booking(client):
    result = book(client)
    assert (
        client.post(
            f"/api/shipments/{result['shipment']['id']}/transition",
            headers={"X-Demo-Role": "dispatch"},
            json={"status": "DELIVERED"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/bookings",
            json={
                "cargo_id": "hero-cargo",
                "vessel_id": "vembanad",
                "mode": "HYBRID",
                "approved": True,
            },
        ).status_code
        == 409
    )


def test_captain_cannot_read_commercial_document_or_margin(client):
    result = book(client)
    captain = {"X-Demo-Role": "captain"}
    workspace = client.get("/api/workspace", headers=captain).json()
    assert "total_cost" not in workspace["shipments"][0]["booking"]
    assert "rate_per_tonne_km" not in workspace["vessels"][0]
    assert (
        client.get(
            f"/api/bookings/{result['booking']['id']}/documents/invoice",
            headers=captain,
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/bookings/{result['booking']['id']}/documents/manifest",
            headers=captain,
        ).status_code
        == 200
    )


def test_route_restriction_has_road_recovery(client):
    result = book(client)
    response = client.post(
        f"/api/bookings/{result['booking']['id']}/disrupt",
        headers={"X-Demo-Role": "dispatch"},
        json={"kind": "ROUTE_CLOSED"},
    )
    assert response.status_code == 200, response.text
    assert any(a["mode"] == "ROAD" for a in response.json()["alternatives"])
