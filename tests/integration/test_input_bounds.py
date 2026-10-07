from io import BytesIO
from openpyxl import load_workbook
from intelligence.document_intake.spreadsheets import template_bytes


def test_large_workbook_returns_bounded_validation_error(client):
    workbook = load_workbook(BytesIO(template_bytes()))
    for _ in range(201):
        workbook.active.append(["overflow"])
    buffer = BytesIO()
    workbook.save(buffer)
    response = client.post(
        "/api/intake/cargo/bulk-preview",
        files={"file": ("large.xlsx", buffer.getvalue())},
    )
    assert response.status_code == 413
    assert "200 rows" in response.text


def test_fleet_duplicate_ids_are_not_counted_twice(client):
    response = client.post(
        "/api/fleet/optimize",
        headers={"X-Demo-Role": "admin"},
        json={"cargo_ids": ["hero-cargo", "hero-cargo"], "vessel_ids": ["vembanad"]},
    )
    assert response.status_code == 422
    assert "unique" in response.text
