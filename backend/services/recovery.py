from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select
from backend.models import *
from backend.repositories.common import require, uid, record, audit
from backend.services.bookings import booking_access, booking_risk, lock_writes
from backend.services.timeutils import dt, utcnow
from backend.services.planning import compare_modes
from optimization.matching.engine import match
from optimization.multimodal.costs import coordinates
from feasibility.engine import check_feasibility


def alternatives(db, booking, actor):
    cargo = require(db, CargoRequest, booking.cargo_id)
    exclusions = (
        [
            b.id
            for b in db.scalars(
                select(Booking).where(Booking.pool_id == booking.pool_id)
            )
        ]
        if booking.pool_id
        else [booking.id]
    )
    matches = match(db, cargo, exclude_booking_ids=exclusions)
    result = []
    for item in matches["recommendations"]:
        if item["vessel_id"] == booking.vessel_id:
            continue
        plan = item["plan"]
        result.append(
            {
                "vessel_id": item["vessel_id"],
                "vessel_name": item["vessel_name"],
                "mode": plan["mode"],
                "plan": plan,
                "additional_cost": round(plan["total_cost"] - booking.total_cost, 2),
                "eta_change_minutes": round(
                    (dt(plan["eta"]) - dt(booking.eta)).total_seconds() / 60
                ),
                "sla": plan["sla"],
                "requires_approval": True,
            }
        )
    road = compare_modes(db, cargo, None)["plans"][0]
    if road["feasible"]:
        result.append(
            {
                "vessel_id": None,
                "vessel_name": "Direct road fallback",
                "mode": "ROAD",
                "plan": road,
                "additional_cost": round(road["total_cost"] - booking.total_cost, 2),
                "eta_change_minutes": round(
                    (dt(road["eta"]) - dt(booking.eta)).total_seconds() / 60
                ),
                "sla": road["sla"],
                "requires_approval": True,
            }
        )
    return {
        "booking_id": booking.id,
        "alternatives": result,
        "requires_approval": True,
        "source": "Deterministic replanning; no consequential rebooking without explicit approval.",
    }


def disrupt(db, actor, booking, kind):
    booking_access(db, actor, booking)
    if booking.status not in {"CONFIRMED", "SCHEDULED", "REPLANNING"}:
        raise HTTPException(
            409,
            "This prototype supports pre-departure recovery. In-voyage intervention requires verified location and a new leg plan.",
        )
    if booking.status in {"DELIVERED", "CANCELLED", "FAILED"}:
        raise HTTPException(409, "A closed booking cannot be disrupted.")
    if kind == "VESSEL_UNAVAILABLE":
        if not booking.vessel_id:
            raise HTTPException(422, "This booking has no vessel.")
        for availability in db.scalars(
            select(VesselAvailability).where(
                VesselAvailability.vessel_id == booking.vessel_id
            )
        ):
            availability.active = False
    elif kind == "ROUTE_CLOSED":
        cargo = db.get(CargoRequest, booking.cargo_id)
        feasible = (
            check_feasibility(
                db,
                cargo,
                db.get(Vessel, booking.vessel_id),
                exclude_booking_ids=[booking.id],
            )
            if booking.vessel_id
            else None
        )
        segment_id = (
            (feasible.get("plan") or {})
            .get("route", {})
            .get("segments", ["segment-2"])[0]
            if feasible
            else "segment-2"
        )
        segment = db.get(WaterwaySegment, segment_id)
        segment.navigation_status = "CLOSED"
        segment.restriction = "Simulated obstruction; demo disruption"
        audit(db, "restriction.created", segment.id, actor, kind=kind)
    else:
        if not booking.destination_terminal_id:
            raise HTTPException(422, "This booking has no terminal.")
        capability = db.scalar(
            select(TerminalCapability).where(
                TerminalCapability.terminal_id == booking.destination_terminal_id
            )
        )
        capability.operational_status = "CLOSED"
    affected = (
        list(
            db.scalars(
                select(Booking).where(
                    Booking.vessel_id == booking.vessel_id,
                    Booking.status.not_in(["DELIVERED", "CANCELLED", "FAILED"]),
                )
            )
        )
        if kind == "VESSEL_UNAVAILABLE"
        else [booking]
    )
    if kind != "VESSEL_UNAVAILABLE":
        candidates = list(
            db.scalars(
                select(Booking).where(
                    Booking.mode != "ROAD",
                    Booking.status.in_(["CONFIRMED", "SCHEDULED", "REPLANNING"]),
                )
            )
        )
        affected = (
            [
                b
                for b in candidates
                if segment_id in b.plan_snapshot.get("route", {}).get("segments", [])
            ]
            if kind == "ROUTE_CLOSED"
            else [
                b
                for b in candidates
                if booking.destination_terminal_id
                in {b.origin_terminal_id, b.destination_terminal_id}
            ]
        )
    for item in affected:
        item.status = "REPLANNING"
        db.get(CargoRequest, item.cargo_id).status = "REPLANNING"
        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == item.id))
        shipment.status = "REPLANNING"
        db.add(
            TrackingEvent(
                id=uid("event"),
                shipment_id=shipment.id,
                status="REPLANNING",
                description=f"{kind}: simulated demo disruption; awaiting approval.",
                latitude=shipment.latitude,
                longitude=shipment.longitude,
            )
        )
        audit(db, "replanning.started", item.id, actor, kind=kind)
    db.commit()
    result = alternatives(db, booking, actor)
    audit(
        db,
        "replanning.completed",
        booking.id,
        actor,
        alternatives=len(result["alternatives"]),
    )
    db.commit()
    return result


def approve_recovery(db, actor, booking, payload):
    booking_access(db, actor, booking)
    if not payload.approved:
        raise HTTPException(422, "Explicit approval is required before rebooking.")
    if booking.status != "REPLANNING":
        raise HTTPException(409, "Booking is not awaiting recovery.")
    lock_writes(db)
    # Each cargo is approved individually. A recovered pooled cargo leaves its
    # old pool; subsequent cargo recovery must fit the replacement reservations.
    cargo = db.get(CargoRequest, booking.cargo_id)
    comparison = compare_modes(
        db, cargo, payload.vessel_id, exclude_booking_ids=[booking.id]
    )
    plan = next(p for p in comparison["plans"] if p["mode"] == payload.mode)
    if not plan["feasible"]:
        raise HTTPException(
            409,
            {
                "message": "Recovery alternative is no longer feasible.",
                "reasons": plan.get("reasons", []),
            },
        )
    if payload.mode != "ROAD" and not payload.vessel_id:
        raise HTTPException(422, "Recovery requires a vessel for water modes.")
    booking.vessel_id = payload.vessel_id if payload.mode != "ROAD" else None
    booking.availability_id = plan.get("availability_id")
    booking.mode = payload.mode
    booking.pool_id = None
    booking.origin_terminal_id = plan.get("origin_terminal_id")
    booking.destination_terminal_id = plan.get("destination_terminal_id")
    booking.total_cost = plan["total_cost"]
    booking.cost_breakdown = plan["breakdown"]
    booking.departure = plan["departure"]
    booking.eta = plan["eta"]
    booking.risk = booking_risk(cargo, plan)
    booking.plan_snapshot = plan
    booking.status = cargo.status = "SCHEDULED"
    shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
    shipment.status = "SCHEDULED"
    for slot in list(
        db.scalars(select(TerminalSlot).where(TerminalSlot.booking_id == booking.id))
    ):
        db.delete(slot)
    if booking.vessel_id:
        for operation, terminal_id, key in [
            ("LOADING", booking.origin_terminal_id, "loading_start"),
            ("UNLOADING", booking.destination_terminal_id, "unloading_start"),
        ]:
            start = dt(plan[key])
            db.add(
                TerminalSlot(
                    id=uid("slot"),
                    terminal_id=terminal_id,
                    booking_id=booking.id,
                    starts_at=start.isoformat(),
                    ends_at=(start + timedelta(hours=0.75)).isoformat(),
                    operation=operation,
                )
            )
    metric = db.scalar(
        select(ImpactMetric).where(ImpactMetric.booking_id == booking.id)
    )
    metric.chosen_cost = booking.total_cost
    metric.chosen_emissions_kg = plan["emissions_kg"]
    metric.tonnes_shifted = cargo.weight_tonnes if booking.vessel_id else 0
    metric.truck_trips_avoided = metric.truck_trips_avoided if booking.vessel_id else 0
    metric.utilization_after = (
        cargo.weight_tonnes / db.get(Vessel, booking.vessel_id).max_capacity_tonnes
        if booking.vessel_id
        else 0
    )
    invoice = db.scalar(
        select(InvoiceRecord).where(InvoiceRecord.booking_id == booking.id)
    )
    payment = db.scalar(
        select(PaymentRecord).where(PaymentRecord.invoice_id == invoice.id)
    )
    if payment.status not in {"PENDING", "DISPUTED"}:
        raise HTTPException(
            409,
            "Paid invoice must be disputed/reconciled before recovery price changes.",
        )
    invoice.total = payment.amount = booking.total_cost
    invoice.line_items = booking.cost_breakdown
    payment.operator_payout = round(
        booking.cost_breakdown.get("water_freight", 0) * 0.95, 2
    )
    db.add(
        TrackingEvent(
            id=uid("event"),
            shipment_id=shipment.id,
            status="SCHEDULED",
            description="Recovery explicitly approved and revalidated.",
            latitude=shipment.latitude,
            longitude=shipment.longitude,
        )
    )
    audit(
        db,
        "booking.recovered",
        booking.id,
        actor,
        mode=payload.mode,
        vessel_id=booking.vessel_id,
    )
    db.commit()
    return {"booking": record(booking), "shipment": record(shipment)}
