import pytest

ADMIN = {"X-Demo-Role": "admin"}


def test_guided_flagship_uses_shared_transactions(client):
    for stage in ["VOICE", "CARGO"]:
        preview = client.post(
            "/api/demo/judge/step", headers=ADMIN, json={"stage": stage}
        )
        assert preview.status_code == 200, preview.text
        assert not preview.json()["complete"]
        approved = client.post(
            "/api/demo/judge/step",
            headers=ADMIN,
            json={"stage": stage, "approved": True},
        )
        assert approved.status_code == 200, approved.text
    for stage in ["FEASIBILITY", "OPTIMIZATION"]:
        assert client.post(
            "/api/demo/judge/step", headers=ADMIN, json={"stage": stage}
        ).json()["complete"]
    booked = client.post(
        "/api/demo/judge/step", headers=ADMIN, json={"stage": "BOOK", "approved": True}
    )
    assert booked.status_code == 200, booked.text
    assert len(booked.json()["result"]["bookings"]) == 2
    start = client.post(
        "/api/demo/judge/step", headers=ADMIN, json={"stage": "START", "approved": True}
    )
    assert start.status_code == 200, start.text
    impact = client.post(
        "/api/demo/judge/step", headers=ADMIN, json={"stage": "IMPACT"}
    ).json()
    assert impact["result"]["tonnes_shifted"] == 138
    assert (
        client.get("/api/impact", headers={"X-Demo-Role": "government"}).json()[
            "tonnes_shifted"
        ]
        == 138
    )


def test_judge_controls_disabled_in_non_demo(client, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "demo_mode", False)
    assert client.post(
        "/api/demo/judge/step", headers=ADMIN, json={"stage": "VOICE"}
    ).status_code in {401, 503}
