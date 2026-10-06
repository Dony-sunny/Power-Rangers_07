import pytest
from backend.models import CargoRequest, Vessel, TerminalCapability, VesselCertificate
from feasibility.engine import check_feasibility
from optimization.matching.engine import match


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("weight_tonnes", 180, "Weight"),
        ("volume_m3", 300, "Volume"),
        ("cargo_type", "chemicals", "category"),
        ("temperature_control_required", True, "Temperature"),
        ("hazardous", True, "Dangerous"),
    ],
)
def test_cargo_constraints(db, field, value, reason):
    cargo = db.get(CargoRequest, "hero-cargo")
    setattr(cargo, field, value)
    result = check_feasibility(db, cargo, db.get(Vessel, "vembanad"))
    assert not result["passed"] and any(reason in r for r in result["reasons"])


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("loaded_draft", 2.3, "draft"),
        ("air_draft", 7, "bridge"),
        ("beam", 14, "beam"),
        ("maintenance_status", "MAINTENANCE", "maintenance"),
    ],
)
def test_vessel_constraints(db, field, value, reason):
    vessel = db.get(Vessel, "vembanad")
    setattr(vessel, field, value)
    result = check_feasibility(db, db.get(CargoRequest, "hero-cargo"), vessel)
    assert not result["passed"] and any(reason in r.lower() for r in result["reasons"])


def test_terminal_equipment_blocks_cargo(db):
    terminal = db.get(TerminalCapability, "capability-alappuzha")
    terminal.forklift_available = False
    result = check_feasibility(
        db, db.get(CargoRequest, "hero-cargo"), db.get(Vessel, "vembanad")
    )
    assert not result["passed"] and any("forklift" in r for r in result["reasons"])


def test_expired_certificate(db):
    db.get(
        VesselCertificate, "vembanad-insurance"
    ).expires_at = "2020-01-01T00:00:00+05:30"
    result = check_feasibility(
        db, db.get(CargoRequest, "hero-cargo"), db.get(Vessel, "vembanad")
    )
    assert not result["passed"] and any("INSURANCE" in r for r in result["reasons"])


def test_matching_is_deterministic_and_excludes_failures(db):
    cargo = db.get(CargoRequest, "hero-cargo")
    first, second = match(db, cargo), match(db, cargo)
    assert first == second
    assert first["recommendations"][0]["vessel_id"] == "vembanad"
    assert "deep-blue" not in {m["vessel_id"] for m in first["recommendations"]}
