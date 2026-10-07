import math
import time
from types import SimpleNamespace
from sqlalchemy import select
from ortools.sat.python import cp_model
from fastapi import HTTPException
from backend.models import *
from backend.repositories.common import uid, record, audit
from backend.services.timeutils import dt
from backend.auth import cargo_access
from feasibility.engine import check_feasibility
from feasibility.cargo_constraints.compatibility import compatible
from feasibility.waterway_constraints.routing import route
from optimization.terminal_selection.planner import node_for


def optimize_fleet(db, actor, payload):
    cargos = list(
        db.scalars(
            select(CargoRequest)
            .where(CargoRequest.id.in_(payload.cargo_ids))
            .order_by(CargoRequest.id)
        )
    )
    vessels = list(
        db.scalars(
            select(Vessel).where(Vessel.id.in_(payload.vessel_ids)).order_by(Vessel.id)
        )
    )
    if len(cargos) != len(set(payload.cargo_ids)) or len(vessels) != len(
        set(payload.vessel_ids)
    ):
        raise HTTPException(404, "A selected cargo or vessel was not found.")
    if actor.role_id == "control":
        for cargo in cargos:
            cargo_access(actor, cargo)
    if actor.role_id == "fleet" and any(
        v.organization_id != actor.organization_id for v in vessels
    ):
        raise HTTPException(404, "Vessel not found in your fleet.")
    if any(
        c.status not in {"POSTED", "MATCHED", "QUOTED"} or c.volume_m3 is None
        for c in cargos
    ):
        raise HTTPException(
            409, "Fleet planning needs unbooked cargo with confirmed volume."
        )
    model = cp_model.CpModel()
    pairs, rejects = {}, []
    for ci, cargo in enumerate(cargos):
        for vi, vessel in enumerate(vessels):
            feasibility = check_feasibility(db, cargo, vessel)
            if not feasibility["passed"]:
                rejects.append(
                    {
                        "cargo_id": cargo.id,
                        "vessel_id": vessel.id,
                        "reasons": feasibility["reasons"],
                    }
                )
                continue
            plan = feasibility["plan"]
            reposition = route(
                db,
                node_for(vessel.current_location),
                db.get(Terminal, plan["origin_terminal_id"]).node_id,
                vessel,
                plan["departure"],
            )
            if not reposition["passed"]:
                rejects.append(
                    {
                        "cargo_id": cargo.id,
                        "vessel_id": vessel.id,
                        "reasons": ["No configured feasible repositioning route"],
                    }
                )
                continue
            if reposition["distance_km"]:
                availability = db.get(VesselAvailability, plan["availability_id"])
                adjusted = SimpleNamespace(**record(cargo))
                from datetime import timedelta

                adjusted.ready_time = max(
                    dt(cargo.ready_time),
                    dt(availability.available_from)
                    + timedelta(hours=reposition["distance_km"] / 10),
                ).isoformat()
                feasibility = check_feasibility(db, adjusted, vessel)
                if not feasibility["passed"]:
                    rejects.append(
                        {
                            "cargo_id": cargo.id,
                            "vessel_id": vessel.id,
                            "reasons": [
                                "Repositioning time makes the requested voyage infeasible"
                            ],
                        }
                    )
                    continue
                plan = feasibility["plan"]
            pairs[ci, vi] = {
                "var": model.new_bool_var(f"cargo_{ci}_vessel_{vi}"),
                "plan": plan,
                "empty_km": reposition["distance_km"],
            }
    for ci in range(len(cargos)):
        model.add(sum(pair["var"] for (c, v), pair in pairs.items() if c == ci) <= 1)
    for vi, vessel in enumerate(vessels):
        eligible = [(ci, pair) for (ci, v), pair in pairs.items() if v == vi]
        if not eligible:
            continue
        capacity = min(pair["plan"]["available_capacity"] for _, pair in eligible)
        volume = min(
            vessel.max_volume_m3,
            *(
                db.get(VesselAvailability, pair["plan"]["availability_id"]).volume_m3
                for _, pair in eligible
            ),
        )
        model.add(
            sum(
                math.ceil(cargos[ci].weight_tonnes * 1000) * pair["var"]
                for ci, pair in eligible
            )
            <= math.floor(capacity * 1000)
        )
        model.add(
            sum(
                math.ceil(cargos[ci].volume_m3 * 1000) * pair["var"]
                for ci, pair in eligible
            )
            <= math.floor(volume * 1000)
        )
        for index, (ci, pair) in enumerate(eligible):
            for cj, other in eligible[index + 1 :]:
                p, q = pair["plan"], other["plan"]
                same_corridor = all(
                    p[key] == q[key]
                    for key in [
                        "origin_terminal_id",
                        "destination_terminal_id",
                        "availability_id",
                    ]
                )
                window_fits = max(dt(p["eta"]), dt(q["eta"])) <= min(
                    dt(cargos[ci].delivery_deadline), dt(cargos[cj].delivery_deadline)
                )
                if (
                    not compatible(cargos[ci], cargos[cj])
                    or not same_corridor
                    or not window_fits
                ):
                    model.add(pair["var"] + other["var"] <= 1)
    objectives = []
    for (ci, vi), pair in pairs.items():
        cargo = cargos[ci]
        vessel = vessels[vi]
        plan = pair["plan"]
        benefit = round(cargo.weight_tonnes * 10000)
        costs = round(plan["total_cost"])
        slack = max(
            0,
            min(
                48,
                (dt(cargo.delivery_deadline) - dt(plan["eta"])).total_seconds() / 3600,
            ),
        )
        utilization = round(cargo.weight_tonnes / vessel.max_capacity_tonnes * 1000)
        penalties = (
            costs
            if payload.objective == "MIN_COST"
            else round(pair["empty_km"] * 1000)
            if payload.objective == "MIN_EMPTY"
            else -utilization * 10
            if payload.objective == "MAX_UTILIZATION"
            else -round(slack * 100)
            if payload.objective == "ON_TIME"
            else costs + round(pair["empty_km"] * 100) - utilization
        )
        objectives.append((benefit * 100 - penalties) * pair["var"])
    model.maximize(sum(objectives))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    started = time.monotonic()
    chosen = []
    for _ in range(4):
        solver.parameters.max_time_in_seconds = max(
            0.1, 3 - (time.monotonic() - started)
        )
        status = solver.solve(model)
        if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            raise HTTPException(
                409,
                "Fleet optimizer found no feasible assignment within its three-second limit.",
            )
        chosen = [
            (key, pair) for key, pair in pairs.items() if solver.value(pair["var"])
        ]
        cuts = False
        for vi, vessel in enumerate(vessels):
            members = [(ci, pair) for (ci, v), pair in chosen if v == vi]
            if not members:
                continue
            cargo = SimpleNamespace(**record(cargos[members[0][0]]))
            from backend.services.terminal_resources import apply_group_requirements

            apply_group_requirements(cargo, [cargos[ci] for ci, _ in members])
            cargo.weight_tonnes = sum(cargos[ci].weight_tonnes for ci, _ in members)
            cargo.volume_m3 = sum(cargos[ci].volume_m3 for ci, _ in members)
            cargo.ready_time = max(
                (pair["plan"]["loading_start"] for _, pair in members), key=dt
            )
            cargo.first_mile_required = False
            origin = db.get(Terminal, members[0][1]["plan"]["origin_terminal_id"])
            origin_node = db.get(WaterwayNode, origin.node_id)
            cargo.origin = origin_node.name
            cargo.origin_coordinates = [origin_node.latitude, origin_node.longitude]
            cargo.delivery_deadline = min(
                (cargos[ci].delivery_deadline for ci, _ in members), key=dt
            )
            cargo.cargo_type = (
                "construction"
                if any(
                    cargos[ci].cargo_type in {"steel", "construction"}
                    for ci, _ in members
                )
                else cargo.cargo_type
            )
            combined = check_feasibility(db, cargo, vessel)
            if not combined["passed"]:
                model.add(sum(pair["var"] for _, pair in members) <= len(members) - 1)
                cuts = True
        if not cuts:
            break
        if time.monotonic() - started >= 3:
            raise HTTPException(
                409,
                "Combined voyage validation requires another search; reduce selected demand.",
            )
    if cuts:
        raise HTTPException(
            409, "No fully revalidated fleet grouping was found within bounded search."
        )
    assignments = []
    for vi, vessel in enumerate(vessels):
        members = [(ci, pair) for (ci, v), pair in chosen if v == vi]
        if not members:
            continue
        tonnes = sum(cargos[ci].weight_tonnes for ci, _ in members)
        assignments.append(
            {
                "vessel_id": vessel.id,
                "vessel_name": vessel.name,
                "cargo_ids": [cargos[ci].id for ci, _ in members],
                "cargo": [
                    {
                        "id": cargos[ci].id,
                        "cargo_type": cargos[ci].cargo_type,
                        "weight_tonnes": cargos[ci].weight_tonnes,
                    }
                    for ci, _ in members
                ],
                "tonnes": tonnes,
                "capacity_tonnes": vessel.max_capacity_tonnes,
                "utilization_pct": round(tonnes / vessel.max_capacity_tonnes * 100, 1),
                "estimated_cost": round(
                    sum(pair["plan"]["total_cost"] for _, pair in members), 2
                ),
                "empty_reposition_km": members[0][1]["empty_km"],
                "mode": members[0][1]["plan"]["mode"],
                "why": [
                    "Each cargo passed hard feasibility.",
                    "Combined weight, volume, co-load rules and voyage windows were revalidated.",
                    "One common-corridor voyage per vessel in this planning horizon.",
                ],
            }
        )
    assigned = {ci for (ci, _), pair in chosen}
    baseline_cost = sum(
        min(pair["plan"]["total_cost"] for (c, _), pair in pairs.items() if c == ci)
        for ci in assigned
    )
    result = {
        "objective": payload.objective,
        "solver": "OR-Tools CP-SAT",
        "solver_status": solver.status_name(status),
        "assignments": assignments,
        "unmatched_cargo_ids": [
            cargos[ci].id for ci in range(len(cargos)) if ci not in assigned
        ],
        "hard_rejections": rejects,
        "before": {
            "utilization_pct": round(
                sum(
                    min(
                        cargos[ci].weight_tonnes / vessels[vi].max_capacity_tonnes
                        for (c, vi) in pairs
                        if c == ci
                    )
                    for ci in assigned
                )
                / max(1, len(assigned))
                * 100,
                1,
            ),
            "estimated_cost": round(baseline_cost, 2),
            "empty_reposition_km": round(
                sum(
                    min(pair["empty_km"] for (c, _), pair in pairs.items() if c == ci)
                    for ci in assigned
                ),
                2,
            ),
        },
        "after": {
            "utilization_pct": round(
                sum(item["utilization_pct"] for item in assignments)
                / max(1, len(assignments)),
                1,
            ),
            "estimated_cost": round(
                sum(item["estimated_cost"] for item in assignments), 2
            ),
            "empty_reposition_km": round(
                sum(item["empty_reposition_km"] for item in assignments), 2
            ),
            "unmatched_cargo": len(cargos) - len(assigned),
        },
        "source": "Computed assignment from synthetic data. One voyage per vessel; not a full multi-tour fleet VRP. Costs conservatively sum per-cargo plans.",
    }
    preview = FleetAssignmentPlan(
        id=uid("fleet-plan"),
        actor_id=actor.id,
        organization_id=actor.organization_id,
        result=result,
    )
    db.add(preview)
    audit(db, "fleet.optimized", preview.id, actor, assignments=len(assignments))
    db.commit()
    return {**result, "plan_id": preview.id, "requires_approval": True}


def approve_fleet(db, actor, plan_id, approved):
    from backend.services.bookings import create_booking, lock_writes
    from backend.schemas.requests import BookingCreate
    from backend.repositories.common import require

    lock_writes(db)
    plan = require(db, FleetAssignmentPlan, plan_id)
    if not approved or plan.approved:
        raise HTTPException(
            409, "Explicit approval required for an unapproved fleet plan."
        )
    if actor.role_id not in {"admin", "control"}:
        raise HTTPException(
            403, "Cross-organization fleet allocation requires control-tower approval."
        )
    results = []
    for assignment in plan.result["assignments"]:
        cargos = [require(db, CargoRequest, key) for key in assignment["cargo_ids"]]
        pool = None
        if len(cargos) > 1:
            pool = PoolingGroup(
                id=uid("pool"),
                vessel_id=assignment["vessel_id"],
                cargo_ids=assignment["cargo_ids"],
                total_tonnes=assignment["tonnes"],
                utilization=assignment["utilization_pct"] / 100,
                solver_status=plan.result["solver_status"],
            )
            db.add(pool)
            db.flush()
        results.append(
            create_booking(
                db,
                actor,
                BookingCreate(
                    cargo_id=cargos[0].id,
                    vessel_id=assignment["vessel_id"],
                    pool_id=pool.id if pool else None,
                    mode=assignment["mode"],
                    approved=True,
                ),
                commit=False,
                acquire_lock=False,
            )
        )
    plan.approved = True
    db.commit()
    return {"assignments_booked": len(results), "results": results}
