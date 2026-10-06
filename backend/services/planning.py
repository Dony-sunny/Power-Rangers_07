from backend.models import Vessel
from backend.repositories.common import require
from feasibility.engine import check_feasibility
from optimization.multimodal.costs import road_plan
from optimization.config import EMISSIONS, RATES


def compare_modes(db, cargo, vessel_id, flood=False, exclude_booking_ids=()):
    road = road_plan(cargo, flood=flood)
    water = {
        "mode": "WATER",
        "feasible": False,
        "total_cost": None,
        "reasons": [
            "Direct water requires terminal-to-terminal cargo; first/last-mile trucking is included under HYBRID."
        ],
    }
    hybrid = {
        "mode": "HYBRID",
        "feasible": False,
        "total_cost": None,
        "reasons": ["Select a feasible vessel to evaluate water plans."],
    }
    feasibility = None
    if vessel_id:
        vessel = require(db, Vessel, vessel_id)
        feasibility = check_feasibility(
            db, cargo, vessel, exclude_booking_ids=exclude_booking_ids
        )
        if feasibility["passed"]:
            plan = feasibility["plan"]
            if plan["mode"] == "WATER":
                water = plan
                hybrid = {
                    **plan,
                    "mode": "HYBRID",
                    "equivalent_to_water": True,
                    "reasons": [
                        "Both endpoints are terminals; zero connecting-road distance."
                    ],
                }
            else:
                hybrid = plan
        else:
            hybrid["reasons"] = feasibility["reasons"]
            water["reasons"] = feasibility["reasons"]
    plans = [road, water, hybrid]
    feasible = [p for p in plans if p["feasible"]]
    best = (
        min(feasible, key=lambda p: (p["total_cost"], p["hours"], p["mode"]))
        if feasible
        else None
    )
    return {
        "plans": plans,
        "recommended_mode": best["mode"] if best else None,
        "explanation": f"{best['mode'].title()} is the lowest delivered-cost plan that meets the requested deadline and constraints."
        if best
        else "No feasible mode meets this request; revise the deadline or route.",
        "emission_factors": EMISSIONS,
        "rates": RATES,
        "source": "Prototype estimates: synthetic rates and straight-line road distance × 1.35; no live tariffs/routing.",
        "feasibility": feasibility,
    }
