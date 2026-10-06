import pytest
from fastapi import HTTPException
from backend.models import (
    CargoRequest,
    Vessel,
    VesselAvailability,
    ScheduledService,
    Booking,
    ScheduledCapacityBooking,
)
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from optimization.scheduled_services.planner import validate_capacity
from datetime import timedelta
from backend.services.timeutils import dt


def test_pooling_capacity_and_hero_utilization(db):
    result = optimize_pool(
        db,
        db.get(CargoRequest, "hero-cargo"),
        db.get(Vessel, "vembanad"),
        persist=False,
    )
    assert result["total_tonnes"] == 138 and result["utilization_after_pct"] == 92
    assert result["total_tonnes"] <= 150


def test_pooling_cargo_compatibility(db):
    db.get(CargoRequest, "hero-cargo").prohibited_co_load_categories = ["steel"]
    result = optimize_pool(
        db,
        db.get(CargoRequest, "hero-cargo"),
        db.get(Vessel, "vembanad"),
        persist=False,
    )
    assert result["total_tonnes"] == 80


def test_backhaul_available_window(db):
    result = find_backhaul(
        db,
        db.get(CargoRequest, "hero-cargo"),
        db.get(Vessel, "vembanad"),
        persist=False,
    )
    assert result["opportunities"][0]["cargo_id"] == "return-cargo"
    return_avail = db.get(VesselAvailability, "availability-vembanad-return")
    return_avail.available_until = (
        dt(return_avail.available_from) + timedelta(minutes=10)
    ).isoformat()
    assert (
        find_backhaul(
            db,
            db.get(CargoRequest, "hero-cargo"),
            db.get(Vessel, "vembanad"),
            persist=False,
        )["opportunities"]
        == []
    )


def test_scheduled_capacity_rejects_overbooking(db):
    cargo = db.get(CargoRequest, "unserved-cargo")
    with pytest.raises(HTTPException):
        validate_capacity(db, db.get(ScheduledService, "nw3-service"), cargo)
