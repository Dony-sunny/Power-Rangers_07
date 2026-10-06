from datetime import timedelta
from data.seed.network import tomorrow


def cargo(client, weight):
    start = tomorrow()
    result = client.post(
        "/api/cargo",
        json={
            "cargo_type": "steel",
            "weight_tonnes": weight,
            "volume_m3": weight * 0.8,
            "packaging": "bundled",
            "origin": "Maradu",
            "destination": "Alappuzha",
            "ready_time": start.isoformat(),
            "delivery_deadline": (start + timedelta(hours=14)).isoformat(),
            "first_mile_required": False,
            "last_mile_required": False,
        },
    )
    assert result.status_code == 201, result.text
    return result.json()["id"]


def test_scheduled_capacity_shared_voyage_and_overflow(client):
    for weight in [60, 35]:
        cargo_id = cargo(client, weight)
        result = client.post(
            "/api/bookings",
            json={
                "cargo_id": cargo_id,
                "vessel_id": "periyar",
                "service_id": "nw3-service",
                "mode": "WATER",
                "approved": True,
            },
        )
        assert result.status_code == 201, result.text
    cargo_id = cargo(client, 10)
    result = client.post(
        "/api/bookings",
        json={
            "cargo_id": cargo_id,
            "vessel_id": "periyar",
            "service_id": "nw3-service",
            "mode": "WATER",
            "approved": True,
        },
    )
    assert result.status_code == 409 and "capacity" in result.text.lower()
    assert (
        client.get("/api/services").json()["services"][0]["remaining_capacity_tonnes"]
        == 5
    )


def test_reject_unsafe_uploads_and_filename_is_sanitized(client):
    result = client.post(
        "/api/intake/cargo/document",
        files={
            "file": (
                "../../evil.txt",
                b"80 tonnes cement from Kochi to Alappuzha",
                "text/plain",
            )
        },
    )
    assert result.status_code == 200 and result.json()["filename"] == "evil.txt"
    assert (
        client.post(
            "/api/intake/cargo/document",
            files={"file": ("script.exe", b"data", "application/octet-stream")},
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/intake/cargo/document",
            files={"file": ("false.pdf", b"not a pdf", "application/pdf")},
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/intake/cargo/document",
            files={"file": ("huge.txt", b"x" * (8 * 1024 * 1024 + 1), "text/plain")},
        ).status_code
        == 413
    )


def test_non_demo_auth_rejects_role_header(client, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "auth_secret", "a" * 32)
    assert (
        client.get("/api/workspace", headers={"X-Demo-Role": "admin"}).status_code
        == 401
    )


def test_broker_runs_real_tools_and_no_automatic_booking(client):
    result = client.post(
        "/api/broker",
        json={
            "text": "Find the best freight plan, pooling and a return load.",
            "cargo_id": "hero-cargo",
        },
    )
    assert result.status_code == 200, result.text
    assert len(result.json()["trace"]) == 4
    assert result.json()["results"]["optimize_load_pool"]["total_tonnes"] == 138
    assert client.get("/api/workspace").json()["shipments"] == []


def test_demo_controls_require_admin_and_reset(client):
    assert client.post("/api/demo/reset").status_code == 403
    assert (
        client.post(
            "/api/demo/scenario",
            headers={"X-Demo-Role": "admin"},
            json={"scenario": "A"},
        ).status_code
        == 200
    )
    assert (
        client.post("/api/demo/reset", headers={"X-Demo-Role": "admin"}).status_code
        == 200
    )
    assert client.get("/api/workspace").json()["shipments"] == []
