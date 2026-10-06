from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.database import get_db
from backend.auth import (
    get_actor,
    permission,
    cargo_access,
    vessel_access,
    GLOBAL_ROLES,
)
from backend.models import CargoRequest, Vessel, ScheduledService, ScheduledServiceStop
from backend.repositories.common import require, record
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from optimization.scheduled_services.planner import segment_usage, propose_services
from feasibility.engine import check_feasibility

router = APIRouter(prefix="/api", tags=["optimization"])


@router.post("/cargo/{cargo_id}/pool")
def pool(cargo_id: str, vessel_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "plan")
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)
    return optimize_pool(
        db,
        cargo,
        require(db, Vessel, vessel_id),
        None if actor.role_id in GLOBAL_ROLES else actor.organization_id,
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
        result.append(
            {
                **record(service),
                "segment_usage": usage,
                "remaining_capacity_tonnes": service.capacity_tonnes
                - max(usage.values(), default=0),
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
