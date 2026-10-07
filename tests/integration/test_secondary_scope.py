from tests.integration.test_evidence_and_admin import booking


def test_operator_own_settlement_visibility_and_captain_redaction(client):
    created = booking(client)
    operator = client.get("/api/workspace", headers={"X-Demo-Role": "operator"}).json()
    assert len(operator["payments"]) == 1
    assert operator["invoices"][0]["booking_id"] == created["booking"]["id"]
    captain = client.get("/api/workspace", headers={"X-Demo-Role": "captain"}).json()
    assert "payments" not in captain and "invoices" not in captain
    assert "total_cost" not in captain["shipments"][0]["booking"]


def test_crew_and_terminal_fields_are_role_scoped(client):
    created = booking(client)
    shipment_id = created["shipment"]["id"]
    endpoint = f"/api/shipments/{shipment_id}/operations"
    assert (
        client.post(
            endpoint,
            headers={"X-Demo-Role": "fleet"},
            json={"crew_assignment": "Demo master and crew"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            endpoint,
            headers={"X-Demo-Role": "fleet"},
            json={"delivery_signature": "Forged receipt"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            endpoint,
            headers={"X-Demo-Role": "warehouse"},
            json={
                "gate_out": True,
                "loading_sequence": ["cement pallets", "verified handover"],
            },
        ).status_code
        == 200
    )
