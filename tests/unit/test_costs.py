from backend.models import CargoRequest
from backend.services.planning import compare_modes
from optimization.multimodal.costs import carbon


def test_cost_totals_and_carbon(db):
    result = compare_modes(db, db.get(CargoRequest, "hero-cargo"), "vembanad")
    assert len(result["plans"]) == 3
    for plan in result["plans"]:
        if plan["total_cost"] is not None:
            assert round(sum(plan["breakdown"].values()), 2) == plan["total_cost"]
    assert carbon(80, 64, "water") == 143.36
    assert carbon(80, 64, "road") == 537.6


def test_urgent_cargo_honestly_recommends_road(db):
    cargo = db.get(CargoRequest, "hero-cargo")
    from datetime import timedelta
    from backend.services.timeutils import dt

    cargo.delivery_deadline = (dt(cargo.ready_time) + timedelta(hours=4)).isoformat()
    result = compare_modes(db, cargo, "vembanad")
    assert result["recommended_mode"] == "ROAD"
