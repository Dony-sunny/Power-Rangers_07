"""Reproduce judge evidence using isolated real services and persisted demo bookings."""

import json
import sys
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timedelta
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import CargoRequest, Vessel, User
from backend.repositories.common import record
from backend.schemas.requests import BookingCreate, RecoveryApproval
from backend.schemas.extensions import PatternCreate, FleetRequest
from backend.services.bookings import create_booking
from backend.services.planning import compare_modes
from backend.services.impact import calculate_impact
from backend.services.recovery import disrupt, approve_recovery
from backend.services.recurring import generate_pattern
from backend.services.analytics import failed_demand
from backend.services.timeutils import IST, dt
from optimization.matching.engine import match
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from optimization.fleet import optimize_fleet
from data.seed.network import seed, tomorrow


@contextmanager
def fixture():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as db:
        seed(db)
        yield db
    engine.dispose()


def generate():
    with fixture() as db:
        cargo = db.get(CargoRequest, "hero-cargo")
        vessel = db.get(Vessel, "vembanad")
        actor = db.get(User, "demo-shipper")
        matched = match(db, cargo, persist=True, actor=actor)
        match(
            db,
            db.get(CargoRequest, "unserved-cargo"),
            persist=True,
            actor=db.get(User, "demo-control"),
        )
        modes = compare_modes(db, cargo, vessel.id)
        terminal_cargo = SimpleNamespace(**record(cargo))
        terminal_cargo.origin = "Maradu"
        terminal_cargo.origin_coordinates = [9.946, 76.325]
        terminal_cargo.first_mile_required = False
        direct_water = next(
            plan
            for plan in compare_modes(db, terminal_cargo, vessel.id)["plans"]
            if plan["mode"] == "WATER"
        )
        urgent = SimpleNamespace(**record(cargo))
        urgent.delivery_deadline = (
            dt(cargo.ready_time) + timedelta(hours=4)
        ).isoformat()
        road_wins = compare_modes(db, urgent, vessel.id)
        pool = optimize_pool(db, cargo, vessel, organization_id=actor.organization_id)
        backhaul = find_backhaul(db, cargo, vessel)
        booked = create_booking(
            db,
            actor,
            BookingCreate(
                cargo_id=cargo.id,
                vessel_id=vessel.id,
                mode="HYBRID",
                pool_id=pool["pool"]["id"],
                approved=True,
            ),
        )
        impact = calculate_impact(db)
        unserved = failed_demand(db)
        road = modes["plans"][0]
        hybrid = modes["plans"][2]
        result = {
            "generated_at": datetime.now(IST).isoformat(),
            "source": "Calculated real application services and persisted bookings in isolated databases. All operational inputs are synthetic.",
            "feasible_vessels": [
                item["vessel_name"] for item in matched["recommendations"]
            ],
            "rejected": [
                {
                    "vessel": item["vessel_name"],
                    "reasons": item["feasibility"]["reasons"],
                }
                for item in matched["rejected"]
            ],
            "individual_modes": modes["plans"],
            "recommended_mode": modes["recommended_mode"],
            "pool": {
                key: pool[key]
                for key in [
                    "total_tonnes",
                    "utilization_before_pct",
                    "utilization_after_pct",
                    "additional_revenue",
                    "solver",
                    "solver_status",
                ]
            },
            "return_opportunities": [
                {
                    key: item[key]
                    for key in [
                        "cargo_type",
                        "weight_tonnes",
                        "revenue",
                        "departure",
                        "eta",
                    ]
                }
                for item in backhaul["opportunities"]
            ],
            "created_bookings": len(booked["bookings"]),
            "booking_impact": impact,
            "judge_metrics": {
                "vessel_utilization_before_pooling_pct": pool["utilization_before_pct"],
                "vessel_utilization_after_pooling_pct": pool["utilization_after_pct"],
                "pooling_tonnes": pool["total_tonnes"],
                "backhaul_opportunity_tonnes": sum(
                    item["weight_tonnes"] for item in backhaul["opportunities"]
                ),
                "road_cost": road["total_cost"],
                "water_cost": modes["plans"][1]["total_cost"],
                "water_infeasibility_reason": modes["plans"][1]["reasons"],
                "hybrid_cost": hybrid["total_cost"],
                "recommended_option": modes["recommended_mode"],
                "individual_cost_difference": round(
                    road["total_cost"] - hybrid["total_cost"], 2
                ),
                "individual_emissions_difference_kg": round(
                    road["emissions_kg"] - hybrid["emissions_kg"], 2
                ),
                "pooled_cost_savings": impact["cost_savings"],
                "pooled_emissions_difference_kg": impact["co2_avoided_kg"],
                "truck_trip_estimate": impact["truck_trips_potentially_avoided"],
                "hard_feasibility_rejections": len(matched["rejected"]),
                "successful_vessel_matches": len(matched["recommendations"]),
                "failed_vessel_matches": len(matched["rejected"]),
                "unserved_demand_tonnes": unserved["unserved_tonnes"],
            },
            "terminal_to_terminal_water_example": {
                "cost": direct_water["total_cost"],
                "origin": "Maradu",
                "destination": "Alappuzha",
                "note": "Separate terminal-to-terminal input; not the door-pickup hero cargo",
            },
            "road_wins": {
                "deadline_window_hours": 4,
                "recommended_mode": road_wins["recommended_mode"],
                "reason": road_wins["explanation"],
            },
        }
        return_booked = create_booking(
            db,
            actor,
            BookingCreate(
                cargo_id="return-cargo",
                vessel_id=vessel.id,
                mode="WATER",
                approved=True,
            ),
        )
        result["booked_backhaul"] = {
            "tonnes": db.get(CargoRequest, "return-cargo").weight_tonnes,
            "counted_backhaul_matches": calculate_impact(db)["backhaul_matches"],
            "created_bookings": len(return_booked["bookings"]),
        }
    with fixture() as db:
        actor = db.get(User, "demo-shipper")
        booking = create_booking(
            db,
            actor,
            BookingCreate(
                cargo_id="hero-cargo",
                vessel_id="vembanad",
                mode="HYBRID",
                approved=True,
            ),
        )
        from backend.models import Booking

        active = db.get(Booking, booking["booking"]["id"])
        dispatch = db.get(User, "demo-dispatch")
        preview = disrupt(db, dispatch, active, "VESSEL_UNAVAILABLE")
        replacement = next(
            item
            for item in preview["alternatives"]
            if item["vessel_id"] == "pamba" and not item.get("service_id")
        )
        recovered = approve_recovery(
            db,
            dispatch,
            active,
            RecoveryApproval(
                vessel_id="pamba", mode=replacement["mode"], approved=True
            ),
        )
        result["recovery"] = {
            "old_cost": booking["booking"]["total_cost"],
            "new_cost": recovered["booking"]["total_cost"],
            "old_eta": booking["booking"]["eta"],
            "new_eta": recovered["booking"]["eta"],
            "cost_impact": replacement["additional_cost"],
            "eta_impact_minutes": replacement["eta_change_minutes"],
            "sla": replacement["sla"],
        }
        result["judge_metrics"]["recovery_cost_impact"] = replacement["additional_cost"]
        result["judge_metrics"]["recovery_eta_impact_minutes"] = replacement[
            "eta_change_minutes"
        ]
    with fixture() as db:
        start = tomorrow().date()
        pattern = generate_pattern(
            db,
            db.get(User, "demo-admin"),
            PatternCreate(
                template_service_id="nw3-service",
                name="Measured recurring demo",
                operating_days=[0, 2, 4],
                departure_time="09:15",
                effective_date=start,
                end_date=start + timedelta(days=14),
                capacity_tonnes=100,
            ),
        )
        result["recurring_service"] = {
            "operating_days": ["Mon", "Wed", "Fri"],
            "generated_departures": len(pattern["service_ids"]),
            "capacity_tonnes": pattern["pattern"]["capacity_tonnes"],
        }
    with fixture() as db:
        fleet = optimize_fleet(
            db,
            db.get(User, "demo-control"),
            FleetRequest(
                cargo_ids=[
                    "hero-cargo",
                    "pool-cargo",
                    "return-cargo",
                    "unserved-cargo",
                ],
                vessel_ids=["vembanad", "pamba", "periyar", "deep-blue"],
            ),
        )
        result["fleet"] = {
            key: fleet[key]
            for key in [
                "solver",
                "solver_status",
                "before",
                "after",
                "unmatched_cargo_ids",
            ]
        }
        result["fleet"]["assignments"] = [
            {
                key: item[key]
                for key in [
                    "vessel_name",
                    "cargo_ids",
                    "tonnes",
                    "capacity_tonnes",
                    "utilization_pct",
                    "empty_reposition_km",
                ]
            }
            for item in fleet["assignments"]
        ]
    return result


if __name__ == "__main__":
    result = generate()
    target = Path(__file__).resolve().parent.parent / "data/demo/measured-results.json"
    target.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(result["judge_metrics"], indent=2))
