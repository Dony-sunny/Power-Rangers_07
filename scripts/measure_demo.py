"""Compute evidence in an isolated database; never mutate the running demo."""

import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import CargoRequest, Vessel, User
from backend.schemas.requests import BookingCreate
from backend.services.bookings import create_booking
from backend.services.planning import compare_modes
from backend.services.impact import calculate_impact
from backend.services.timeutils import IST
from optimization.matching.engine import match
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from data.seed.network import seed

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
with sessionmaker(bind=engine, expire_on_commit=False)() as db:
    seed(db)
    cargo = db.get(CargoRequest, "hero-cargo")
    vessel = db.get(Vessel, "vembanad")
    actor = db.get(User, "demo-shipper")
    matched = match(db, cargo)
    modes = compare_modes(db, cargo, vessel.id)
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
    result = {
        "generated_at": datetime.now(IST).isoformat(),
        "source": "Calculated application results using synthetic demo inputs, isolated database",
        "feasible_vessels": [m["vessel_name"] for m in matched["recommendations"]],
        "rejected": [
            {"vessel": m["vessel_name"], "reasons": m["feasibility"]["reasons"]}
            for m in matched["rejected"]
        ],
        "individual_modes": modes["plans"],
        "recommended_mode": modes["recommended_mode"],
        "pool": {
            k: pool[k]
            for k in [
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
                k: item[k]
                for k in ["cargo_type", "weight_tonnes", "revenue", "departure", "eta"]
            }
            for item in backhaul["opportunities"]
        ],
        "created_bookings": len(booked["bookings"]),
        "booking_impact": calculate_impact(db),
    }
    target = Path(__file__).resolve().parent.parent / "data/demo/measured-results.json"
    target.parent.mkdir(exist_ok=True, parents=True)
    target.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "pool": result["pool"],
                "shifted_tonnes": result["booking_impact"]["tonnes_shifted"],
                "estimated_cost_savings": result["booking_impact"]["cost_savings"],
                "estimated_co2_avoided_kg": result["booking_impact"]["co2_avoided_kg"],
            },
            indent=2,
        )
    )
