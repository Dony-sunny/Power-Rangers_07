from io import BytesIO
from pathlib import Path
from openpyxl import load_workbook
from backend.models import ScheduledService, CargoRequest
from intelligence.document_intake.spreadsheets import template_bytes
from intelligence.document_intake.ocr import run_ocr
from tests.integration.test_scheduling_extensions import pattern, ADMIN
from tests.integration.test_evidence_and_admin import booking, delivery_stage, RECEIVER


def test_actual_scanned_pdf_uses_local_ocr():
    result = run_ocr(Path("data/demo/scanned_purchase_order.pdf").read_bytes(), ".pdf")
    assert result["source"] == "local_onnx_ocr", result
    assert "80 tonnes cement" in result["text"]
    assert "Ready" in result["text"]


def test_duplicate_workbook_headers_are_rejected(client):
    workbook = load_workbook(BytesIO(template_bytes()))
    workbook.active["N1"] = "weight"
    output = BytesIO()
    workbook.save(output)
    response = client.post(
        "/api/intake/cargo/bulk-preview",
        files={"file": ("ambiguous.xlsx", output.getvalue())},
    )
    assert response.status_code == 422
    assert "Duplicate" in response.text


def test_recurring_failure_after_first_write_rolls_back_everything(client, db):
    schedule = pattern(client)
    db.get(ScheduledService, schedule["service_ids"][1]).active = False
    db.commit()
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
    assert db.get(CargoRequest, "pool-cargo").status == "POSTED"


def test_fleet_never_pools_prohibited_categories(client, db):
    cargo = db.get(CargoRequest, "hero-cargo")
    cargo.prohibited_co_load_categories = ["steel"]
    db.commit()
    response = client.post(
        "/api/fleet/optimize",
        headers=ADMIN,
        json={
            "cargo_ids": ["hero-cargo", "pool-cargo"],
            "vessel_ids": ["vembanad"],
            "objective": "MAX_UTILIZATION",
        },
    )
    assert response.status_code == 200, response.text
    assert all(
        len(assignment["cargo"]) == 1 for assignment in response.json()["assignments"]
    )


def test_otp_locks_after_five_wrong_attempts(client):
    created = booking(client)
    shipment_id = created["shipment"]["id"]
    delivery_stage(client, shipment_id)
    challenge = client.post(
        f"/api/shipments/{shipment_id}/delivery-challenge", headers=RECEIVER
    ).json()
    wrong = "000000" if challenge["demo_otp"] != "000000" else "111111"
    endpoint = f"/api/delivery-challenges/{challenge['challenge_id']}/verify"
    for _ in range(5):
        assert (
            client.post(endpoint, headers=RECEIVER, json={"code": wrong}).status_code
            == 422
        )
    assert (
        client.post(
            endpoint, headers=RECEIVER, json={"code": challenge["demo_otp"]}
        ).status_code
        == 409
    )
