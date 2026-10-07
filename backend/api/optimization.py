from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.database import get_db
from backend.auth import (
    get_actor,
    permission,
    cargo_access,
    vessel_access,
    GLOBAL_ROLES,
    coordinated_orgs,
)
from backend.models import CargoRequest, Vessel, ScheduledService, ScheduledServiceStop
from backend.repositories.common import require, record
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from optimization.scheduled_services.planner import segment_usage, propose_services
from feasibility.engine import check_feasibility

router = APIRouter(prefix="/api", tags=["optimization"])


from backend.schemas.extensions import FleetRequest
from optimization.fleet import optimize_fleet, approve_fleet


@router.get("/fleet/demand")
def fleet_demand(db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id not in {"fleet", "control", "admin"}:
        raise HTTPException(403, "Fleet demand requires operations permissions.")
    vessels = [
        vessel
        for vessel in db.scalars(select(Vessel))
        if actor.role_id in {"control", "admin"}
        or vessel.organization_id == actor.organization_id
    ]
    return {
        "cargo": [
            {
                key: getattr(cargo, key)
                for key in [
                    "id",
                    "cargo_type",
                    "weight_tonnes",
                    "volume_m3",
                    "origin",
                    "destination",
                ]
            }
            for cargo in db.scalars(select(CargoRequest))
            if cargo.status in {"POSTED", "MATCHED", "QUOTED"}
            and cargo.volume_m3 is not None
            and (actor.role_id != "control" or cargo.organization_id in coordinated_orgs(db, actor))
        ],
        "vessels": [
            {
                "id": vessel.id,
                "name": vessel.name,
                "max_capacity_tonnes": vessel.max_capacity_tonnes,
            }
            for vessel in vessels
        ],
    }


@router.post("/fleet/optimize")
def fleet_plan(payload: FleetRequest, db=Depends(get_db), actor=Depends(get_actor)):
    if actor.role_id not in {"fleet", "control", "admin"}:
        raise HTTPException(
            403, "Fleet optimization requires fleet or control permissions."
        )
    return optimize_fleet(db, actor, payload)


@router.post("/fleet/plans/{plan_id}/approve")
def fleet_approval(
    plan_id: str, approved: bool = False, db=Depends(get_db), actor=Depends(get_actor)
):
    return approve_fleet(db, actor, plan_id, approved)


@router.post("/cargo/{cargo_id}/pool")
def pool(cargo_id: str, vessel_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    return optimize_pool(
        db,
        cargo,
        require(db, Vessel, vessel_id),
        None if actor.role_id in GLOBAL_ROLES | {"control"} else actor.organization_id,
        actor=actor,
    )


@router.post("/cargo/{cargo_id}/backhaul")
def backhaul(
    cargo_id: str, vessel_id: str, db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    return find_backhaul(db, cargo, require(db, Vessel, vessel_id), actor=actor)


@router.get("/vessels/{vessel_id}/opportunities")
def opportunities(vessel_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "vessel_write")
    vessel = require(db, Vessel, vessel_id)
    vessel_access(actor, vessel)
    cargos = []
    for cargo in db.scalars(select(CargoRequest)):
        if cargo.status not in {"POSTED", "MATCHED", "QUOTED"}:
            continue
        feasible = check_feasibility(db, cargo, vessel)
        if feasible["passed"]:
            cargos.append((cargo, feasible))
    cargos.sort(key=lambda item: (-item[0].weight_tonnes, item[0].id))
    if not cargos:
        return {"cargo": [], "pool": None, "backhaul": None}
    anchor = cargos[0][0]
    try:
        pool = optimize_pool(db, anchor, vessel, persist=False)
    except HTTPException:
        pool = None
    return {
        "cargo": [
            {
                "id": c.id,
                "cargo_type": c.cargo_type,
                "weight_tonnes": c.weight_tonnes,
                "origin": c.origin,
                "destination": c.destination,
                "eta": f["plan"]["eta"],
                "estimated_freight_revenue": f["plan"]["breakdown"]["water_freight"],
            }
            for c, f in cargos
        ],
        "pool": pool,
        "backhaul": find_backhaul(db, anchor, vessel, persist=False),
    }


@router.get("/services")
def services(db=Depends(get_db), actor=Depends(get_actor)):
    result = []
    for service in db.scalars(select(ScheduledService)):
        usage = segment_usage(db, service)
        from backend.services.recurring import segment_limit

        limits = {sequence: segment_limit(db, service, sequence) for sequence in usage}
        result.append(
            {
                **record(service),
                "segment_usage": usage,
                "segment_capacities": limits,
                "booked_tonnes": max(usage.values(), default=0),
                "projected_utilization_pct": round(
                    max(usage.values(), default=0) / service.capacity_tonnes * 100, 1
                ),
                "remaining_capacity_tonnes": min(
                    (limits[sequence] - usage[sequence] for sequence in usage),
                    default=service.capacity_tonnes,
                )
                if service.active
                else 0,
                "stops": [
                    record(s)
                    for s in db.scalars(
                        select(ScheduledServiceStop)
                        .where(ScheduledServiceStop.service_id == service.id)
                        .order_by(ScheduledServiceStop.sequence)
                    )
                ],
            }
        )
    return {
        "services": result,
        "proposals": propose_services(db) if actor.role_id in GLOBAL_ROLES else [],
    }
