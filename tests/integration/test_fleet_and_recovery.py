import pytest

CONTROL = {"X-Demo-Role": "control"}
DISPATCH = {"X-Demo-Role": "dispatch"}


def test_fleet_assignment_capacity_and_hard_constraints(client):
    response = client.post(
        "/api/fleet/optimize",
        headers=CONTROL,
        json={
            "cargo_ids": ["hero-cargo", "pool-cargo", "unserved-cargo"],
            "vessel_ids": ["vembanad", "pamba", "deep-blue"],
            "objective": "BALANCED",
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["solver_status"] in {"OPTIMAL", "FEASIBLE"}
    assert "unserved-cargo" in result["unmatched_cargo_ids"]
    assert all(
        item["tonnes"] <= item["capacity_tonnes"] for item in result["assignments"]
    )
    assert all(item["vessel_id"] != "deep-blue" for item in result["assignments"])
    approval = client.post(
        f"/api/fleet/plans/{result['plan_id']}/approve?approved=true", headers=CONTROL
    )
    assert approval.status_code == 200, approval.text
    assert len(client.get("/api/workspace", headers=CONTROL).json()["shipments"]) == 2


def test_fleet_requires_operations_role(client):
    assert (
        client.post(
            "/api/fleet/optimize",
            json={"cargo_ids": ["hero-cargo"], "vessel_ids": ["vembanad"]},
        ).status_code
        == 403
    )


def test_whole_pool_recovery_is_atomic_and_capacity_checked(client):
    pool = client.post("/api/cargo/hero-cargo/pool?vessel_id=vembanad").json()["pool"]
    booked = client.post(
        "/api/bookings",
        json={
            "cargo_id": "hero-cargo",
            "vessel_id": "vembanad",
            "pool_id": pool["id"],
            "mode": "HYBRID",
            "approved": True,
        },
    ).json()
    booking_id = booked["booking"]["id"]
    assert (
        client.post(
            f"/api/bookings/{booking_id}/disrupt",
            headers=DISPATCH,
            json={"kind": "VESSEL_UNAVAILABLE"},
        ).status_code
        == 200
    )
    response = client.post(
        f"/api/bookings/{booking_id}/recover-pool",
        headers=DISPATCH,
        json={"vessel_id": "pamba", "mode": "HYBRID", "approved": True},
    )
    assert response.status_code == 200, response.text
    assert response.json()["recovered_count"] == 2
    assert all(
        item["booking"]["vessel_id"] == "pamba"
        for item in client.get("/api/workspace").json()["shipments"]
    )


@pytest.mark.parametrize(
    "kind",
    ["EQUIPMENT_UNAVAILABLE", "SHIPMENT_NOT_READY", "TRUCK_LATE", "CAPACITY_REDUCED"],
)
def test_complex_disruptions_return_revalidated_alternatives(client, kind):
    booked = client.post(
        "/api/bookings",
        json={
            "cargo_id": "hero-cargo",
            "vessel_id": "vembanad",
            "mode": "HYBRID",
            "approved": True,
        },
    ).json()
    response = client.post(
        f"/api/bookings/{booked['booking']['id']}/disrupt",
        headers=DISPATCH,
        json={"kind": kind, "delay_minutes": 30, "capacity_tonnes": 50},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["alternatives"]
    assert result["old_plan"]["eta"] == booked["booking"]["eta"]
    assert all(
        item["plan"]["feasible"] and item["requires_approval"]
        for item in result["alternatives"]
    )
