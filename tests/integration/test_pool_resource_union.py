from sqlalchemy import select
from backend.models import CargoRequest, ResourceReservation, TerminalResource


def test_pool_reserves_equipment_required_by_non_anchor_member(client, db):
    db.get(CargoRequest, "hero-cargo").packaging = "bulk"
    db.get(CargoRequest, "pool-cargo").packaging = "pallets"
    db.commit()
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
    )
    assert booked.status_code == 201, booked.text
    kinds = {
        db.get(TerminalResource, item.resource_id).kind
        for item in db.scalars(select(ResourceReservation))
    }
    assert {"CRANE", "FORKLIFT"} <= kinds
