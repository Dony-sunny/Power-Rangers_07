from datetime import timedelta
from sqlalchemy import delete, select
from backend.models import (
    FreightRateObservation,
    NavigationReport,
    RouteRestriction,
    TrackingEvent,
    Shipment,
    Booking,
)
from intelligence.document_intake.spreadsheets import template_bytes
from backend.services.timeutils import dt

GOVERNMENT = {"X-Demo-Role": "government"}
NETWORK = {"X-Demo-Role": "network"}


def test_rate_benchmark_real_formula_and_small_sample_behavior(client, db):
    result = client.get(
        "/api/cargo/hero-cargo/rate-benchmark?vessel_id=vembanad"
    ).json()
    assert result["sample_size"] == 5
    assert result["status"] == "WITHIN_RANGE"
    db.execute(delete(FreightRateObservation))
    db.commit()
    result = client.get(
        "/api/cargo/hero-cargo/rate-benchmark?vessel_id=vembanad"
    ).json()
    assert (
        result["status"] == "INSUFFICIENT_HISTORY" and result["range_per_tonne"] is None
    )


def test_failed_demand_reason_aggregation_unique_tonnage(client):
    for _ in range(2):
        assert (
            client.get(
                "/api/cargo/unserved-cargo/matches", headers={"X-Demo-Role": "admin"}
            ).status_code
            == 200
        )
    result = client.get("/api/intelligence/failed-demand", headers=GOVERNMENT).json()
    row = next(item for item in result["rows"] if item["cargo_id"] == "unserved-cargo")
    assert "NO_CAPACITY" in row["reasons"]
    assert row["search_count"] == 2 and row["tonnes"] == 240
    client.post("/api/cargo/hero-cargo/reject-quote")
    result = client.get("/api/intelligence/failed-demand", headers=GOVERNMENT).json()
    assert next(item for item in result["rows"] if item["cargo_id"] == "hero-cargo")[
        "reasons"
    ] == ["PRICE_REJECTED"]


def test_modal_shift_xlsx_upload_computed(client):
    response = client.post(
        "/api/intelligence/modal-shift/upload",
        headers=GOVERNMENT,
        files={"file": ("history.xlsx", template_bytes())},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["total_shipments_analyzed"] == 1
    # Fixed sailing charges can leave this historical load cheaper on road.
    assert result["rows"][0]["suitability"] == "MEDIUM"
    assert result["candidate_tonnes"] == 80
    assert result["estimated_co2_difference_kg"] > 0


def test_crowd_report_review_does_not_implicitly_close_route(client, db):
    response = client.post(
        "/api/reports",
        headers={"X-Demo-Role": "captain"},
        json={
            "segment_id": "segment-2",
            "report_type": "SHALLOW",
            "description": "Shallow area reported",
            "coordinates": [9.74, 76.39],
            "confidence": 0.6,
        },
    )
    assert response.status_code == 201
    report = response.json()
    assert report["verification_status"] == "UNVERIFIED"
    assert (
        client.patch(
            f"/api/reports/{report['id']}",
            json={
                "verification_status": "VERIFIED",
                "confidence": 0.8,
                "note": "Reviewed operator report",
            },
        ).status_code
        == 403
    )
    reviewed = client.patch(
        f"/api/reports/{report['id']}",
        headers=NETWORK,
        json={
            "verification_status": "VERIFIED",
            "confidence": 0.8,
            "note": "Reviewed operator report",
        },
    )
    assert reviewed.status_code == 200 and reviewed.json()["restriction_id"] is None
    assert not list(db.scalars(select(RouteRestriction)))
    promoted = client.patch(
        f"/api/reports/{report['id']}",
        headers=NETWORK,
        json={
            "verification_status": "VERIFIED",
            "confidence": 0.8,
            "note": "Conservative platform closure",
            "promote_restriction": True,
        },
    )
    assert promoted.json()["restriction_id"]


def test_corridor_uses_recorded_events_and_insufficient_history(client, db):
    created = client.post(
        "/api/bookings",
        json={
            "cargo_id": "hero-cargo",
            "vessel_id": "vembanad",
            "mode": "HYBRID",
            "approved": True,
        },
    ).json()
    for status in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING", "DELIVERED"]:
        assert (
            client.post(
                f"/api/shipments/{created['shipment']['id']}/transition",
                headers={"X-Demo-Role": "dispatch"},
                json={"status": status},
            ).status_code
            == 200
        )
    events = list(
        db.scalars(
            select(TrackingEvent).where(
                TrackingEvent.shipment_id == created["shipment"]["id"]
            )
        )
    )
    start = dt(created["booking"]["departure"])
    for event in events:
        if event.status == "IN_TRANSIT":
            event.timestamp = start.isoformat()
        if event.status == "UNLOADING":
            event.timestamp = (start + timedelta(hours=6)).isoformat()
        if event.status == "DELIVERED":
            event.timestamp = (start + timedelta(hours=7)).isoformat()
    db.commit()
    result = client.get("/api/intelligence/corridors", headers=GOVERNMENT).json()[
        "corridors"
    ][0]
    assert result["sample_size"] == 1 and result["median_transit_hours"] == 6
    assert (
        result["reliability_score"] is None
        and result["history_status"] == "Insufficient history"
    )
