"""Reproduce the three-role Cargo Lines demo in isolated SQLite databases."""
import json
import sys
from pathlib import Path
from contextlib import contextmanager
from datetime import timedelta
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import CargoRequest, Vessel, User, CargoVoyage, ProviderJob
from backend.services import cargo_lines as lines
from backend.services.line_planning import build_plan
from backend.services.terminal_resources import seed_resources
from backend.services.timeutils import utcnow, dt
from backend.api.cargo_lines import advice
from optimization.matching.engine import match
from optimization.multimodal.costs import road_plan
from optimization.multimodal.trip_costs import TERMS
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from data.seed.network import seed

@contextmanager
def fixture():
    engine = create_engine("sqlite://")
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as db:
        seed(db)
        seed_resources(db)
        db.commit()
        yield db
    engine.dispose()

def accept_and_confirm(db, voyage, operator_user="demo-operator"):
    shipper, control, operator = [db.get(User, key) for key in ["demo-shipper", "demo-control", operator_user]]
    for member in lines.members(db, voyage):
        lines.approve_quote(db, shipper, member.quote_id)
    lines.operator_response(db, operator, voyage.id, voyage.version, True)
    for job in lines.jobs(db, voyage):
        lines.job_response(db, control, job.id, "ACCEPTED")
    return lines.confirm(db, control, voyage.id)

def generate():
    with fixture() as db:
        cargo, vessel = db.get(CargoRequest, "hero-cargo"), db.get(Vessel, "vembanad")
        shipper, control = db.get(User, "demo-shipper"), db.get(User, "demo-control")
        matched = match(db, cargo, persist=True, actor=shipper)
        cost_advice = advice(cargo.id, vessel.id, True, db, shipper)
        existing_58 = build_plan(db, [db.get(CargoRequest, "pool-cargo")], vessel)
        pool = optimize_pool(db, cargo, vessel, organization_id=shipper.organization_id, persist=False)
        backhaul = find_backhaul(db, cargo, vessel)
        proposed = lines.propose(db, shipper, [cargo.id, "pool-cargo"], vessel.id)
        voyage = db.get(CargoVoyage, proposed["id"])
        confirmed = accept_and_confirm(db, voyage)
        selected = lines.impact(db, control)
        customer_prices = [{"cargo_id": m["cargo_id"], "total_minor": m["quote"]["total_minor"], "total_cost": m["quote"]["total_cost"], "invoice_total": m["invoice"]["total"], "eta": m["eta"], "rate_cards": m["quote"]["snapshot"]["rate_card_ids"]} for m in confirmed["members"]]
        for status in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"]:
            lines.milestones(db, control, voyage.id, status)
        for member in confirmed["members"]:
            lines.receipt(db, control, voyage.id, member["cargo_id"], member["weight_tonnes"], "Alappuzha demo receiver")
        completed = lines.impact(db, control)
        chosen = sum(p["total_cost"] for p in customer_prices)
        road_total = sum(m["quote"]["snapshot"]["road_baseline"]["total_cost"] for m in confirmed["members"])
        metrics = {
            "pooled_tonnes": confirmed["weight_tonnes"],
            "utilization_pct": round(confirmed["utilization"] * 100, 1),
            "modeled_sailing_contribution": confirmed["accepted_economics"]["contribution_minor"] / 100,
            "accepted_delivery_revenue": confirmed["accepted_economics"]["revenue_minor"] / 100,
            "modeled_payables_and_operating_allowance": confirmed["accepted_economics"]["operating_cost_minor"] / 100,
            "existing_58t_contribution": existing_58["economics"]["contribution_minor"] / 100,
            "whole_pickup_trucks": sum(j["kind"] == "PICKUP_TRUCK" for j in confirmed["jobs"]),
            "provider_jobs": len(confirmed["jobs"]),
            "individual_road_cost": cost_advice["road"]["total_cost"],
            "individual_water_truck_cost": cost_advice["water"]["total_cost"],
            "pooled_customer_cost": round(chosen, 2),
            "pooled_road_baseline": round(road_total, 2),
            "pooled_modeled_cost_difference": round(road_total - chosen, 2),
            "selected_water_tonnes": selected["selected_water_tonnes"],
            "completed_water_tonnes": completed["completed_water_tonnes"],
            "estimated_full_delivery_co2_difference_kg": selected["estimated_full_delivery_co2_avoided_kg"],
            "long_haul_truck_equivalents": selected["long_haul_truck_equivalents"],
            "connecting_truck_trips": selected["connecting_truck_trips"],
        }
        result = {
            "generated_at": utcnow().isoformat(),
            "source": "Actual application services, immutable quotes, accepted simulated jobs, bookings and receipts in isolated SQLite. All rates, operating terms, geometry and emission factors are synthetic.",
            "tariff": TERMS,
            "judge_metrics": metrics,
            "matching_recommendations": [{"vessel_id": r["vessel_id"], "name": r["vessel_name"]} for r in matched["recommendations"]],
            "rejected": [{"vessel": r["vessel_name"], "reasons": r["feasibility"]["reasons"]} for r in matched["rejected"]],
            "cost_advisor": cost_advice,
            "customer_quotes": customer_prices,
            "accepted_economics": confirmed["accepted_economics"],
            "selected_impact": selected,
            "completed_impact": completed,
            "pool_solver": {"solver": pool["solver"], "status": pool["solver_status"], "selected_tonnes": pool["total_tonnes"]},
            "return_opportunities": [{"cargo_type": r["cargo_type"], "weight_tonnes": r["weight_tonnes"], "source": "Opportunity only; excluded from all contribution and impact totals"} for r in backhaul["opportunities"]],
            "confirmation_evidence": {"owner_quotes_approved": confirmed["owners_ready"], "operator_accepted_version": voyage.operator_accepted_version, "accepted_jobs": confirmed["accepted_job_count"], "job_count": confirmed["job_count"]},
        }
    with fixture() as db:
        shipper, control = db.get(User, "demo-shipper"), db.get(User, "demo-control")
        proposal = lines.propose(db, shipper, ["hero-cargo", "pool-cargo"], "vembanad")
        voyage = db.get(CargoVoyage, proposal["id"])
        confirmed = accept_and_confirm(db, voyage)
        old_total = sum(m["quote"]["total_minor"] for m in confirmed["members"])
        lines.disrupt(db, control, voyage.id)
        offers = lines.recovery_options(db, control, voyage)
        replacement = next(o for o in offers["options"] if o["vessel_id"] == "pamba")
        fresh = lines.propose(db, control, replacement["cargo_ids"], "pamba", voyage.id)
        recovered = accept_and_confirm(db, db.get(CargoVoyage, fresh["id"]), "demo-pamba-operator")
        new_total = sum(m["quote"]["total_minor"] for m in recovered["members"])
        result["pre_pickup_recovery"] = {"original_vessel": "vembanad", "replacement_vessel": "pamba", "old_total_minor": old_total, "new_total_minor": new_total, "approved_difference": (new_total - old_total) / 100, "all_new_quotes_approved": recovered["owners_ready"], "replacement_operator_accepted": recovered["operator_accepted"], "all_new_provider_jobs_accepted": recovered["providers_ready"], "original_invoice_state": "VOID", "source": "SIMULATED; no pickup has occurred"}
    return result

if __name__ == "__main__":
    result = generate()
    target = Path(__file__).resolve().parent.parent / "data/demo/measured-results.json"
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["judge_metrics"], indent=2))
