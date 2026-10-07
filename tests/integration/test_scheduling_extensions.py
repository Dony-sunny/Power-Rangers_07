from datetime import timedelta
from data.seed.network import tomorrow

ADMIN = {"X-Demo-Role": "admin"}


def pattern(client, segment_cap=100):
    start = tomorrow().date()
    response = client.post(
        "/api/service-patterns",
        headers=ADMIN,
        json={
            "template_service_id": "nw3-service",
            "name": "Recurring NW-3 freight",
            "operating_days": list(range(7)),
            "departure_time": "09:15",
            "effective_date": start.isoformat(),
            "end_date": (start + timedelta(days=3)).isoformat(),
            "capacity_tonnes": 100,
            "segment_capacities": {"0": segment_cap},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_recurring_departures_and_bookings(client):
    schedule = pattern(client)
    assert len(schedule["service_ids"]) == 4
    response = client.post(
        "/api/services/recurring-bookings",
        json={
            "cargo_id": "pool-cargo",
            "service_ids": schedule["service_ids"][:2],
            "approved": True,
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["booking_count"] == 2
    cancelled = client.post(
        f"/api/services/{schedule['service_ids'][0]}/cancel", headers=ADMIN
    )
    assert cancelled.json()["pattern_preserved"]
    assert len(cancelled.json()["affected_bookings"]) == 1
    states = client.get("/api/service-patterns").json()["occurrences"]
    assert sum(item["status"] == "SCHEDULED" for item in states) == 3


def test_segment_capacity_and_atomic_recurring_failure(client):
    schedule = pattern(client, 50)
    response = client.post(
        "/api/services/recurring-bookings",
        json={
            "cargo_id": "pool-cargo",
            "service_ids": schedule["service_ids"][:2],
            "approved": True,
        },
    )
    assert response.status_code == 409
    assert not client.get("/api/workspace").json()["shipments"]


def test_contract_reserved_capacity_subtracts_from_market(client):
    schedule = pattern(client)
    start = tomorrow().date()
    response = client.post(
        "/api/capacity-contracts",
        json={
            "pattern_id": schedule["pattern"]["id"],
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=3)).isoformat(),
            "weekly_commitment_tonnes": 350,
            "tonnes_per_departure": 60,
            "rate_per_tonne": 300,
            "minimum_commitment_tonnes": 120,
            "start_sequence": 0,
            "end_sequence": 3,
        },
    )
    assert response.status_code == 201, response.text
    service = next(
        item
        for item in client.get("/api/services").json()["services"]
        if item["id"] == schedule["service_ids"][0]
    )
    assert service["remaining_capacity_tonnes"] == 40
    result = client.post(
        "/api/bookings",
        json={
            "cargo_id": "pool-cargo",
            "vessel_id": "periyar",
            "service_id": service["id"],
            "contract_id": response.json()["contract"]["id"],
            "mode": "HYBRID",
            "approved": True,
        },
    )
    assert result.status_code == 201, result.text
    service = next(
        item
        for item in client.get("/api/services").json()["services"]
        if item["id"] == service["id"]
    )
    assert (
        service["remaining_capacity_tonnes"] == 40
    )  # Draw does not double count the hold.


def test_terminal_berth_and_equipment_collisions(client):
    inventory = client.get("/api/terminals/resources", headers=ADMIN).json()
    start = tomorrow()
    for kind in ["BERTH", "CRANE"]:
        resource = next(item for item in inventory["resources"] if item["kind"] == kind)
        payload = {
            "resource_id": resource["id"],
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=1)).isoformat(),
            "quantity": 1,
        }
        assert (
            client.post(
                "/api/terminals/reservations", headers=ADMIN, json=payload
            ).status_code
            == 201
        )
        collision = client.post(
            "/api/terminals/reservations", headers=ADMIN, json=payload
        )
        assert collision.status_code == 409
        assert "Suggested next start" in collision.text


def test_manual_terminal_reservation_delays_real_plan(client):
    resources = client.get("/api/terminals/resources", headers=ADMIN).json()[
        "resources"
    ]
    forklift = next(
        item
        for item in resources
        if item["terminal_id"] == "terminal-maradu" and item["kind"] == "FORKLIFT"
    )
    start = tomorrow()
    assert (
        client.post(
            "/api/terminals/reservations",
            headers=ADMIN,
            json={
                "resource_id": forklift["id"],
                "starts_at": start.isoformat(),
                "ends_at": (start + timedelta(hours=3)).isoformat(),
                "quantity": 1,
            },
        ).status_code
        == 201
    )
    plan = client.get("/api/cargo/hero-cargo/compare?vessel_id=vembanad").json()
    selected = next(
        item for item in plan["plans"] if item["mode"] == plan["recommended_mode"]
    )
    assert selected["feasible"]
