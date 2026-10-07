import math
from sqlalchemy import select
from ortools.sat.python import cp_model
from fastapi import HTTPException
from backend.models import CargoRequest, PoolingGroup
from backend.repositories.common import uid, record, audit
from backend.services.timeutils import dt
from feasibility.engine import check_feasibility
from feasibility.cargo_constraints.compatibility import compatible
from optimization.terminal_selection.planner import node_for


def optimize_pool(db, anchor, vessel, organization_id=None, persist=True, actor=None):
    if anchor.status not in {"POSTED", "MATCHED", "QUOTED"}:
        raise HTTPException(409, "Pooling requires unbooked cargo.")
    feasibility = check_feasibility(db, anchor, vessel)
    if not feasibility["passed"]:
        raise HTTPException(
            409,
            {
                "message": "Vessel failed hard feasibility.",
                "reasons": feasibility["reasons"],
            },
        )
    if anchor.volume_m3 is None:
        raise HTTPException(409, "Confirm cargo volume before pooling.")
    plan = feasibility["plan"]
    eligible = []
    for cargo in db.scalars(select(CargoRequest).order_by(CargoRequest.id)):
        if actor and actor.role_id == "control":
            from backend.auth import coordinated_orgs
            if cargo.organization_id not in coordinated_orgs(db, actor):
                continue
        if (
            organization_id
            and cargo.organization_id != organization_id
            or cargo.status not in {"POSTED", "MATCHED", "QUOTED"}
        ):
            continue
        if (
            cargo.volume_m3 is None
            or cargo.id != anchor.id
            and not compatible(anchor, cargo)
        ):
            continue
        if node_for(cargo.origin) != node_for(anchor.origin) or node_for(
            cargo.destination
        ) != node_for(anchor.destination):
            continue
        candidate = check_feasibility(db, cargo, vessel)
        if not candidate["passed"]:
            continue
        p = candidate["plan"]
        if (
            p["origin_terminal_id"] != plan["origin_terminal_id"]
            or p["destination_terminal_id"] != plan["destination_terminal_id"]
        ):
            continue
        eligible.append((cargo, p))
    if anchor.id not in {c.id for c, _ in eligible}:
        raise HTTPException(
            409, "Anchor cargo is not eligible for a synchronized pool."
        )
    model = cp_model.CpModel()
    variables = [model.new_bool_var(c.id) for c, _ in eligible]
    # Conservative integer rounding: weights/volumes round up; limits round down.
    model.add(
        sum(
            math.ceil(c.weight_tonnes * 1000) * v
            for (c, _), v in zip(eligible, variables)
        )
        <= math.floor(plan["available_capacity"] * 1000)
    )
    model.add(
        sum(math.ceil(c.volume_m3 * 1000) * v for (c, _), v in zip(eligible, variables))
        <= math.floor(vessel.max_volume_m3 * 1000)
    )
    for i, (cargo, cargo_plan) in enumerate(eligible):
        if cargo.id == anchor.id:
            model.add(variables[i] == 1)
        for j in range(i + 1, len(eligible)):
            other, other_plan = eligible[j]
            synchronized_arrival = max(dt(cargo_plan["eta"]), dt(other_plan["eta"]))
            incompatible = not compatible(cargo, other) or synchronized_arrival > min(
                dt(cargo.delivery_deadline), dt(other.delivery_deadline)
            )
            if incompatible:
                model.add(variables[i] + variables[j] <= 1)
    model.maximize(
        sum(
            (
                round(c.weight_tonnes * 1000) * 100000
                + round(c.weight_tonnes * plan["water_km"] * vessel.rate_per_tonne_km)
                - 100
            )
            * v
            for (c, _), v in zip(eligible, variables)
        )
    )
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.solve(model)
    if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        raise HTTPException(409, "No feasible load pool found within the solver limit.")
    chosen = [
        cargo for (cargo, _), var in zip(eligible, variables) if solver.value(var)
    ]
    total = sum(c.weight_tonnes for c in chosen)
    group = PoolingGroup(
        id=uid("pool"),
        vessel_id=vessel.id,
        cargo_ids=[c.id for c in chosen],
        total_tonnes=total,
        utilization=total / vessel.max_capacity_tonnes,
        solver_status=solver.status_name(status),
    )
    if persist:
        db.add(group)
        audit(
            db,
            "pool.created",
            group.id,
            actor,
            total_tonnes=total,
            cargo_count=len(chosen),
        )
        db.commit()
    return {
        "pool": record(group),
        "cargo": [
            {
                "id": c.id,
                "cargo_type": c.cargo_type,
                "weight_tonnes": c.weight_tonnes,
                "volume_m3": c.volume_m3,
            }
            for c in chosen
        ],
        "total_tonnes": total,
        "utilization_before_pct": round(
            anchor.weight_tonnes / vessel.max_capacity_tonnes * 100, 1
        ),
        "utilization_after_pct": round(total / vessel.max_capacity_tonnes * 100, 1),
        "additional_revenue": round(
            (total - anchor.weight_tonnes)
            * plan["water_km"]
            * vessel.rate_per_tonne_km,
            2,
        ),
        "solver": "OR-Tools CP-SAT",
        "solver_status": group.solver_status,
        "objective": "Maximize compatible tonnage, then estimated freight revenue; penalize extra handling. Zero route deviation within a common terminal corridor.",
        "source": "Synthetic demo inputs; calculated optimization output",
    }
