from sqlalchemy import select
from backend.models import (
    Vessel,
    CargoRequest,
    MatchRecommendation,
    ComplianceCheck,
    TransportQuote,
)
from backend.repositories.common import uid, audit
from backend.services.timeutils import dt
from feasibility.engine import check_feasibility
from optimization.multimodal.costs import road_plan
from optimization.config import PROFILES
from feasibility.cargo_constraints.compatibility import compatible
from optimization.terminal_selection.planner import node_for


def match(
    db, cargo, profile="BALANCED", persist=False, actor=None, exclude_booking_ids=()
):
    weights = PROFILES.get(profile)
    if weights is None:
        raise ValueError("Unknown ranking profile.")
    candidates, rejected = [], []
    road = road_plan(cargo)
    for vessel in db.scalars(select(Vessel).order_by(Vessel.id)):
        feasibility = check_feasibility(
            db, cargo, vessel, exclude_booking_ids=exclude_booking_ids
        )
        capacity_fit = min(1, cargo.weight_tonnes / vessel.max_capacity_tonnes)
        if not feasibility["passed"]:
            rejected.append(
                {
                    "vessel_id": vessel.id,
                    "vessel_name": vessel.name,
                    "reliability": vessel.reliability_score,
                    "commercial_rate": vessel.rate_per_tonne_km,
                    "feasibility": feasibility,
                    "commercial_score": round(
                        100
                        * (
                            0.5 * vessel.reliability_score
                            + 0.5 * min(1, 3 / vessel.rate_per_tonne_km)
                        ),
                        1,
                    ),
                }
            )
            if persist:
                db.add(
                    MatchRecommendation(
                        id=uid("match"),
                        cargo_id=cargo.id,
                        vessel_id=vessel.id,
                        passed=False,
                        score=0,
                        explanation={"reasons": feasibility["reasons"]},
                    )
                )
                db.add(
                    ComplianceCheck(
                        id=uid("check"),
                        vessel_id=vessel.id,
                        cargo_id=cargo.id,
                        passed=False,
                        reasons=feasibility["reasons"],
                    )
                )
                audit(
                    db,
                    "feasibility.failed",
                    vessel.id,
                    actor,
                    cargo_id=cargo.id,
                    reasons=feasibility["reasons"],
                )
            continue
        plan = feasibility["plan"]
        projected_weight = cargo.weight_tonnes
        projected_volume = cargo.volume_m3 or 0
        for other in db.scalars(select(CargoRequest).order_by(CargoRequest.id)):
            if (
                other.id == cargo.id
                or other.status not in {"POSTED", "MATCHED", "QUOTED"}
                or not compatible(cargo, other)
            ):
                continue
            if node_for(other.origin) != node_for(cargo.origin) or node_for(
                other.destination
            ) != node_for(cargo.destination):
                continue
            if max(dt(other.ready_time), dt(cargo.ready_time)) >= min(
                dt(other.delivery_deadline), dt(cargo.delivery_deadline)
            ):
                continue
            if (
                projected_weight + other.weight_tonnes <= plan["available_capacity"]
                and other.volume_m3 is not None
                and projected_volume + other.volume_m3 <= vessel.max_volume_m3
            ):
                projected_weight += other.weight_tonnes
                projected_volume += other.volume_m3
        window = max(
            1,
            (dt(cargo.delivery_deadline) - dt(cargo.ready_time)).total_seconds() / 3600,
        )
        factors = {
            "capacity": projected_weight / vessel.max_capacity_tonnes,
            "schedule": max(0, min(1, 1 - plan["hours"] / window)),
            "cost": 1
            / (1 + plan["total_cost"] / (road.get("total_cost") or plan["total_cost"])),
            "reliability": vessel.reliability_score,
            "carbon": max(
                0, 1 - plan["emissions_kg"] / max(1, road.get("emissions_kg", 1))
            ),
        }
        score = round(sum(factors[key] * weights[key] * 100 for key in weights), 2)
        reasons = [
            f"Hard physical and operational constraints passed.",
            f"{capacity_fit * 100:.1f}% individual utilization; {projected_weight / vessel.max_capacity_tonnes * 100:.1f}% potential with a compatible pool (preview).",
            f"{vessel.reliability_score * 100:.0f}% operator reliability (demo history).",
            f"Full delivered cost ₹{plan['total_cost']:,.0f}; ETA fits the requested window.",
        ]
        item = {
            "vessel_id": vessel.id,
            "vessel_name": vessel.name,
            "capacity_tonnes": vessel.max_capacity_tonnes,
            "reliability": vessel.reliability_score,
            "score": score,
            "factors": factors,
            "weights": weights,
            "reasons": reasons,
            "feasibility": feasibility,
            "plan": plan,
        }
        candidates.append(item)
        if persist:
            db.add(
                MatchRecommendation(
                    id=uid("match"),
                    cargo_id=cargo.id,
                    vessel_id=vessel.id,
                    passed=True,
                    score=score,
                    explanation={
                        "factors": factors,
                        "weights": weights,
                        "reasons": reasons,
                    },
                )
            )
            db.add(
                ComplianceCheck(
                    id=uid("check"),
                    vessel_id=vessel.id,
                    cargo_id=cargo.id,
                    passed=True,
                    reasons=[],
                )
            )
            db.add(
                TransportQuote(
                    id=uid("quote"),
                    cargo_id=cargo.id,
                    vessel_id=vessel.id,
                    mode=plan["mode"],
                    total=plan["total_cost"],
                    breakdown=plan["breakdown"],
                    eta=plan["eta"],
                    reliability=vessel.reliability_score,
                )
            )
    candidates.sort(key=lambda item: (-item["score"], item["vessel_id"]))
    if persist:
        from backend.services.analytics import record_search

        record_search(db, cargo, candidates, rejected)
        if cargo.status in {"POSTED", "MATCHED", "QUOTED"}:
            cargo.status = "QUOTED" if candidates else "POSTED"
        audit(
            db,
            "match.generated",
            cargo.id,
            actor,
            feasible=len(candidates),
            rejected=len(rejected),
        )
        db.commit()
    return {
        "cargo_id": cargo.id,
        "profile": profile,
        "recommendations": candidates,
        "rejected": rejected,
        "source": "Deterministic ranking; synthetic demo operations",
    }
