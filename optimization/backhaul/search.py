from datetime import timedelta
from types import SimpleNamespace
from sqlalchemy import select
from backend.models import (
    CargoRequest,
    BackhaulOpportunity,
    Booking,
    VesselAvailability,
)
from backend.repositories.common import uid, record, audit
from backend.services.timeutils import dt
from feasibility.engine import check_feasibility
from optimization.terminal_selection.planner import node_for


def find_backhaul(db, outbound, vessel, actor=None, persist=True):
    booking = db.scalar(
        select(Booking)
        .where(
            Booking.cargo_id == outbound.id,
            Booking.vessel_id == vessel.id,
            Booking.status.not_in(["CANCELLED", "FAILED"]),
        )
        .order_by(Booking.created_at.desc())
    )
    if booking:
        arrival = dt(booking.eta)
    else:
        feasible = check_feasibility(db, outbound, vessel)
        if not feasible["passed"]:
            return {"opportunities": [], "reasons": feasible["reasons"]}
        arrival = dt(feasible["plan"]["eta"])
    ready = arrival + timedelta(hours=1)
    opportunities = []
    for cargo in db.scalars(select(CargoRequest).order_by(CargoRequest.id)):
        if (
            cargo.status not in {"POSTED", "MATCHED", "QUOTED"}
            or node_for(cargo.origin) != node_for(outbound.destination)
            or node_for(cargo.destination) != node_for(outbound.origin)
        ):
            continue
        adjusted = SimpleNamespace(**record(cargo))
        adjusted.ready_time = max(dt(cargo.ready_time), ready).isoformat()
        feasible = check_feasibility(db, adjusted, vessel)
        if not feasible["passed"]:
            continue
        plan = feasible["plan"]
        revenue = plan["breakdown"]["water_freight"]
        opportunities.append(
            {
                "cargo_id": cargo.id,
                "cargo_type": cargo.cargo_type,
                "weight_tonnes": cargo.weight_tonnes,
                "origin": cargo.origin,
                "destination": cargo.destination,
                "departure": plan["departure"],
                "eta": plan["eta"],
                "revenue": revenue,
                "empty_return_avoided_if_booked": True,
                "reasons": [
                    "Reverse corridor matches outbound voyage.",
                    "Verified against actual return availability, cargo readiness and deadlines.",
                    "One-hour prototype turnaround included.",
                ],
                "plan": plan,
            }
        )
        if persist:
            db.add(
                BackhaulOpportunity(
                    id=uid("backhaul"),
                    vessel_id=vessel.id,
                    cargo_id=cargo.id,
                    outbound_cargo_id=outbound.id,
                    revenue=revenue,
                    departure=plan["departure"],
                )
            )
    opportunities.sort(key=lambda p: (-p["revenue"], p["cargo_id"]))
    if persist and opportunities:
        audit(db, "backhaul.found", outbound.id, actor, count=len(opportunities))
        db.commit()
    return {
        "opportunities": opportunities,
        "outbound_arrival": arrival.isoformat(),
        "turnaround_hours": 1,
        "source": "Deterministic return-window search, synthetic fixtures; no reservation until confirmed.",
    }
