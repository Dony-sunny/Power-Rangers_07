from io import BytesIO
from datetime import timedelta
from PIL import Image
from sqlalchemy import select
from backend.models import DeliveryChallenge
from backend.services.timeutils import utcnow

ADMIN = {"X-Demo-Role": "admin"}
RECEIVER = {"X-Demo-Role": "receiver"}
DISPATCH = {"X-Demo-Role": "dispatch"}


def booking(client):
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


def delivery_stage(client, shipment_id):
    for status in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"]:
        assert (
            client.post(
                f"/api/shipments/{shipment_id}/transition",
                headers=DISPATCH,
                json={"status": status},
            ).status_code
            == 200
        )


def test_photos_validate_and_remain_authorized(client):
    created = booking(client)
    shipment_id = created["shipment"]["id"]
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/photos",
            headers=RECEIVER,
            files={"file": ("fake.jpg", b"fake", "image/jpeg")},
        ).status_code
        == 415
    )
    output = BytesIO()
    Image.new("RGB", (32, 32), "green").save(output, "PNG")
    response = client.post(
        f"/api/shipments/{shipment_id}/photos",
        headers=RECEIVER,
        files={"file": ("cargo.png", output.getvalue(), "image/png")},
        data={"category": "POD", "description": "Receiver evidence"},
    )
    assert response.status_code == 201, response.text
    photo = response.json()
    assert "image_base64" not in photo
    assert (
        client.get(f"/api/photos/{photo['id']}", headers=RECEIVER)
        .json()["data_url"]
        .startswith("data:image/jpeg")
    )
    assert (
        client.get(
            f"/api/photos/{photo['id']}", headers={"X-Demo-User": "competitor-user"}
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/photos",
            headers=RECEIVER,
            files={"file": ("large.jpg", b"0" * (2 * 1024 * 1024 + 1))},
        ).status_code
        == 413
    )


def test_opaque_qr_label_does_not_grant_access(client):
    created = booking(client)
    response = client.get(f"/api/labels/shipment/{created['shipment']['id']}")
    assert response.status_code == 200, response.text
    label = response.json()
    assert len(label["reference"].removeprefix("label-")) == 32
    assert "<svg" in label["qr_svg"]
    assert "80" not in label["payload"] or "label-" in label["payload"]
    assert created["shipment"]["id"] not in label["payload"]
    assert (
        client.get(
            "/api/labels/" + label["reference"],
            headers={"X-Demo-User": "competitor-user"},
        ).status_code
        == 404
    )
    assert client.get("/api/labels/" + label["reference"]).json()["weight_tonnes"] == 80
    for kind, identifier in [
        ("booking", created["booking"]["id"]),
        ("cargo", "hero-cargo"),
    ]:
        assert client.get(f"/api/labels/{kind}/{identifier}/print").status_code == 200


def test_delivery_otp_hash_expiry_and_verification(client, db):
    created = booking(client)
    shipment_id = created["shipment"]["id"]
    delivery_stage(client, shipment_id)
    issued = client.post(
        f"/api/shipments/{shipment_id}/delivery-challenge", headers=RECEIVER
    )
    assert issued.status_code == 200, issued.text
    challenge = issued.json()
    stored = db.get(DeliveryChallenge, challenge["challenge_id"])
    assert stored.otp_hash != challenge["demo_otp"] and len(stored.otp_hash) > 6
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/transition",
            headers=DISPATCH,
            json={"status": "DELIVERED"},
        ).status_code
        == 409
    )
    assert client.post(
        f"/api/delivery-challenges/{stored.id}/verify",
        headers=RECEIVER,
        json={"code": challenge["demo_otp"]},
    ).json()["verified"]
    assert (
        client.post(
            f"/api/shipments/{shipment_id}/transition",
            headers=DISPATCH,
            json={"status": "DELIVERED"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/delivery-challenges/{stored.id}/verify",
            headers=RECEIVER,
            json={"code": challenge["demo_otp"]},
        ).status_code
        == 409
    )


def test_otp_expired_and_bad_attempt_limit(client, db):
    created = booking(client)
    shipment_id = created["shipment"]["id"]
    delivery_stage(client, shipment_id)
    issued = client.post(
        f"/api/shipments/{shipment_id}/delivery-challenge", headers=RECEIVER
    ).json()
    challenge = db.get(DeliveryChallenge, issued["challenge_id"])
    challenge.expires_at = (utcnow() - timedelta(seconds=1)).isoformat()
    db.commit()
    assert (
        client.post(
            f"/api/delivery-challenges/{challenge.id}/verify",
            headers=RECEIVER,
            json={"code": issued["demo_otp"]},
        ).status_code
        == 409
    )


def test_admin_membership_roles_and_disable(client):
    payload = {"name": "Pilot organization", "kind": "shipper"}
    assert client.post("/api/admin/organizations", json=payload).status_code == 403
    organization = client.post(
        "/api/admin/organizations", headers=ADMIN, json=payload
    ).json()
    response = client.post(
        "/api/admin/users",
        headers=ADMIN,
        json={
            "name": "Pilot user",
            "organization_id": organization["id"],
            "role_id": "shipper",
        },
    )
    assert response.status_code == 201, response.text
    user = response.json()
    assert (
        client.patch(
            f"/api/admin/users/{user['id']}",
            headers=ADMIN,
            json={"role_id": "dispatch"},
        ).json()["role_id"]
        == "dispatch"
    )
    assert (
        client.get(
            "/api/workspace",
            headers={"X-Demo-Role": "dispatch", "X-Demo-User": user["id"]},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/admin/users/{user['id']}", headers=ADMIN, json={"disabled": True}
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/api/workspace",
            headers={"X-Demo-Role": "dispatch", "X-Demo-User": user["id"]},
        ).status_code
        == 403
    )
    assert (
        client.patch(
            "/api/admin/users/demo-admin", headers=ADMIN, json={"disabled": True}
        ).status_code
        == 409
    )
