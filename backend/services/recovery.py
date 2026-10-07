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
                "reason": "Revalidated departure, vessel and terminal pair. Same-vessel options can change timing or terminals.",
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
                "reason": "Road fallback rechecks readiness and delivery SLA.",
            }
        )
    from optimization.scheduled_services.planner import service_plan, validate_capacity

    for service in db.scalars(
        select(ScheduledService).where(ScheduledService.active == True)
    ):
        if service.vessel_id == booking.vessel_id and booking.status != "REPLANNING":
            continue
        try:
            validate_capacity(db, service, cargo)
            comparison = compare_modes(
                db, cargo, service.vessel_id, exclude_booking_ids=exclusions
            )
            preview = next(
                p for p in comparison["plans"] if p["feasible"] and p["mode"] != "ROAD"
            )
            plan = service_plan(db, service, cargo, preview)
            result.append(
                {
                    "vessel_id": service.vessel_id,
                    "service_id": service.id,
                    "vessel_name": service.name,
                    "mode": plan["mode"],
                    "plan": plan,
                    "additional_cost": round(
                        plan["total_cost"] - booking.total_cost, 2
                    ),
                    "eta_change_minutes": round(
                        (dt(plan["eta"]) - dt(booking.eta)).total_seconds() / 60
                    ),
                    "sla": plan["sla"],
                    "requires_approval": True,
                    "reason": "Alternative dated scheduled service; capacity and stop windows revalidated.",
                }
            )
        except (HTTPException, StopIteration):
            continue
    result.sort(
        key=lambda item: (
            not item["sla"],
            item["plan"]["total_cost"],
            item["plan"]["eta"],
            -item["plan"]["reliability"],
            item["plan"]["emissions_kg"],
        )
    )
    return {
        "booking_id": booking.id,
        "alternatives": result,
        "requires_approval": True,
        "old_plan": {
            "mode": booking.mode,
            "cost": booking.total_cost,
            "eta": booking.eta,
            "vessel_id": booking.vessel_id,
        },
        "affected_booking_ids": [
            item.id
            for item in db.scalars(
                select(Booking).where(Booking.pool_id == booking.pool_id)
            )
        ]
        if booking.pool_id
        else [booking.id],
        "ranking": "SLA, delivered cost, ETA, reliability, then emissions. Plans remain approval previews.",
        "source": "Deterministic replanning; no consequential rebooking without explicit approval.",
    }


def disrupt(db, actor, booking, kind, details=None):
    details = details or {}
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
    elif kind == "TERMINAL_CLOSED":
        if not booking.destination_terminal_id:
            raise HTTPException(422, "This booking has no terminal.")
        capability = db.scalar(
            select(TerminalCapability).where(
                TerminalCapability.terminal_id == booking.destination_terminal_id
            )
        )
        capability.operational_status = "CLOSED"
    elif kind == "EQUIPMENT_UNAVAILABLE":
        if not booking.destination_terminal_id:
            raise HTTPException(422, "No terminal equipment belongs to this booking.")
        for resource in db.scalars(
            select(TerminalResource).where(
                TerminalResource.terminal_id == booking.destination_terminal_id,
                TerminalResource.kind.in_(["CRANE", "FORKLIFT"]),
            )
        ):
            resource.active = False
    elif kind in {"SHIPMENT_NOT_READY", "TRUCK_LATE"}:
        cargo = db.get(CargoRequest, booking.cargo_id)
        cargo.ready_time = (
            max(dt(cargo.ready_time), dt(booking.departure))
            + timedelta(minutes=details.get("delay_minutes", 60))
        ).isoformat()
    elif kind == "CAPACITY_REDUCED":
        if not booking.vessel_id:
            raise HTTPException(422, "No vessel capacity belongs to this booking.")
        vessel = db.get(Vessel, booking.vessel_id)
        limit = details.get("capacity_tonnes") or max(
            1, vessel.max_capacity_tonnes * 0.5
        )
        if limit >= vessel.max_capacity_tonnes:
            raise HTTPException(422, "Reduced capacity must be below vessel capacity.")
        for availability in db.scalars(
            select(VesselAvailability).where(VesselAvailability.vessel_id == vessel.id)
        ):
            availability.capacity_tonnes = min(availability.capacity_tonnes, limit)
        for service in db.scalars(
            select(ScheduledService).where(ScheduledService.vessel_id == vessel.id)
        ):
            service.capacity_tonnes = min(service.capacity_tonnes, limit)
    elif kind == "SERVICE_CANCELLED":
        capacity = db.scalar(
            select(ScheduledCapacityBooking).where(
                ScheduledCapacityBooking.booking_id == booking.id
            )
        )
        if not capacity:
            raise HTTPException(422, "Booking does not use a scheduled service.")
        service = db.get(ScheduledService, capacity.service_id)
        service.active = False
        occurrence = db.scalar(
            select(ServiceOccurrence).where(ServiceOccurrence.service_id == service.id)
        )
        if occurrence:
            occurrence.status = "CANCELLED"
    affected = (
        list(
            db.scalars(
                select(Booking).where(
                    Booking.vessel_id == booking.vessel_id,
                    Booking.status.not_in(["DELIVERED", "CANCELLED", "FAILED"]),
                )
            )
        )
        if kind in {"VESSEL_UNAVAILABLE", "CAPACITY_REDUCED"}
        else [booking]
    )
    if kind in {"ROUTE_CLOSED", "TERMINAL_CLOSED", "EQUIPMENT_UNAVAILABLE"}:
        candidates = list(
            db.scalars(
                select(Booking).where(
                    Booking.mode != "ROAD",
                    Booking.status.in_(["CONFIRMED", "SCHEDULED", "REPLANNING"]),
                )
            )
        )
    elif kind == "SERVICE_CANCELLED":
        affected = [
            db.get(Booking, item.booking_id)
            for item in db.scalars(
                select(ScheduledCapacityBooking).where(
                    ScheduledCapacityBooking.service_id == service.id
                )
            )
            if db.get(Booking, item.booking_id).status
            in {"CONFIRMED", "SCHEDULED", "REPLANNING"}
        ]
    elif booking.pool_id and kind in {"SHIPMENT_NOT_READY", "TRUCK_LATE"}:
        affected = list(
            db.scalars(
                select(Booking).where(
                    Booking.pool_id == booking.pool_id,
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
        db.add(
            DisruptionRecord(
                id=uid("disruption"), booking_id=item.id, kind=kind, detail=details
            )
        )
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


def approve_recovery(
    db,
    actor,
    booking,
    payload,
    commit=True,
    acquire_lock=True,
    exclusions=(),
    plan_override=None,
    reserve_resources=True,
):
    booking_access(db, actor, booking)
    if not payload.approved:
        raise HTTPException(422, "Explicit approval is required before rebooking.")
    if booking.status != "REPLANNING":
        raise HTTPException(409, "Booking is not awaiting recovery.")
    if acquire_lock:
        lock_writes(db)
    # Each cargo is approved individually. A recovered pooled cargo leaves its
    # old pool; subsequent cargo recovery must fit the replacement reservations.
    cargo = db.get(CargoRequest, booking.cargo_id)
    comparison = compare_modes(
        db,
        cargo,
        payload.vessel_id,
        exclude_booking_ids=list(exclusions) or [booking.id],
    )
    plan = plan_override or next(
        p for p in comparison["plans"] if p["mode"] == payload.mode
    )
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
    for capacity in list(
        db.scalars(
            select(ScheduledCapacityBooking).where(
                ScheduledCapacityBooking.booking_id == booking.id
            )
        )
    ):
        db.delete(capacity)
    for draw in list(
        db.scalars(select(ContractDraw).where(ContractDraw.booking_id == booking.id))
    ):
        db.delete(draw)
    service = None
    if payload.service_id:
        from optimization.scheduled_services.planner import (
            validate_capacity,
            service_plan,
        )

        service = require(db, ScheduledService, payload.service_id)
        if payload.mode == "ROAD" or service.vessel_id != payload.vessel_id:
            raise HTTPException(422, "Recovery service and vessel must agree.")
        start, end = validate_capacity(db, service, cargo)
        plan = service_plan(db, service, cargo, plan)
        db.add(
            ScheduledCapacityBooking(
                id=uid("capacity"),
                service_id=service.id,
                cargo_id=cargo.id,
                booking_id=booking.id,
                weight_tonnes=cargo.weight_tonnes,
                start_sequence=start.sequence,
                end_sequence=end.sequence,
            )
        )
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
    for reservation in list(
        db.scalars(
            select(ResourceReservation).where(
                ResourceReservation.booking_id == booking.id
            )
        )
    ):
        db.delete(reservation)
    for leg in list(
        db.scalars(select(ShipmentLeg).where(ShipmentLeg.shipment_id == shipment.id))
    ):
        db.delete(leg)
    legs = (
        [("ROAD", cargo.origin, cargo.destination)]
        if payload.mode == "ROAD"
        else (
            [("ROAD", cargo.origin, plan["origin_terminal"])]
            if plan.get("first_mile_km")
            else []
        )
        + [("WATER", plan["origin_terminal"], plan["destination_terminal"])]
        + (
            [("ROAD", plan["destination_terminal"], cargo.destination)]
            if cargo.last_mile_required
            else []
        )
    )
    for sequence, (mode, origin, destination) in enumerate(legs):
        db.add(
            ShipmentLeg(
                id=uid("leg"),
                shipment_id=shipment.id,
                mode=mode,
                origin=origin,
                destination=destination,
                sequence=sequence,
                assigned_provider=db.get(Vessel, payload.vessel_id).name
                if mode == "WATER"
                else None,
            )
        )
    db.flush()
    if booking.vessel_id and reserve_resources:
        from backend.services.terminal_resources import reserve_plan

        reserve_plan(
            db,
            booking,
            cargo,
            db.get(Vessel, booking.vessel_id),
            service.id if service else None,
        )
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
    if commit:
        db.commit()
    return {"booking": record(booking), "shipment": record(shipment)}


def approve_pool_recovery(db, actor, booking, payload):
    from types import SimpleNamespace
    from feasibility.cargo_constraints.compatibility import compatible
    from backend.services.terminal_resources import reserve_plan

    booking_access(db, actor, booking)
    if not payload.approved or not booking.pool_id or payload.service_id:
        raise HTTPException(
            422,
            "Approve a common-voyage pool recovery without a scheduled-service selection.",
        )
    lock_writes(db)
    members = list(
        db.scalars(select(Booking).where(Booking.pool_id == booking.pool_id))
    )
    if any(member.status != "REPLANNING" for member in members):
        raise HTTPException(
            409, "Every pool member must await recovery before coordinated approval."
        )
    for member in members:
        booking_access(db, actor, member)
    exclusions = [member.id for member in members]
    cargos = [db.get(CargoRequest, member.cargo_id) for member in members]
    if any(
        not compatible(first, second)
        for index, first in enumerate(cargos)
        for second in cargos[index + 1 :]
    ):
        raise HTTPException(
            409, "Pool cargo compatibility changed; review individual alternatives."
        )
    plans = []
    for cargo in cargos:
        comparison = compare_modes(
            db, cargo, payload.vessel_id, exclude_booking_ids=exclusions
        )
        plan = next(p for p in comparison["plans"] if p["mode"] == payload.mode)
        if not plan["feasible"]:
            raise HTTPException(409, "A pool member failed recovery feasibility.")
        plans.append(plan)
    pool = None
    combined = None
    if payload.mode != "ROAD":
        vessel = require(db, Vessel, payload.vessel_id)
        merged = SimpleNamespace(**record(cargos[0]))
        from backend.services.terminal_resources import apply_group_requirements

        apply_group_requirements(merged, cargos)
        merged.weight_tonnes = sum(c.weight_tonnes for c in cargos)
        merged.volume_m3 = sum(c.volume_m3 or 0 for c in cargos)
        merged.ready_time = max((plan["loading_start"] for plan in plans), key=dt)
        origin = db.get(Terminal, plans[0]["origin_terminal_id"])
        node = db.get(WaterwayNode, origin.node_id)
        merged.origin = node.name
        merged.origin_coordinates = [node.latitude, node.longitude]
        merged.first_mile_required = False
        merged.delivery_deadline = min(
            (cargo.delivery_deadline for cargo in cargos), key=dt
        )
        merged.cargo_type = (
            "construction"
            if any(c.cargo_type in {"steel", "construction"} for c in cargos)
            else merged.cargo_type
        )
        feasible = check_feasibility(db, merged, vessel, exclude_booking_ids=exclusions)
        if not feasible["passed"]:
            raise HTTPException(
                409,
                {
                    "message": "Combined replacement failed hard feasibility.",
                    "reasons": feasible["reasons"],
                },
            )
        combined = feasible["plan"]
        if any(
            plan["origin_terminal_id"] != combined["origin_terminal_id"]
            or plan["destination_terminal_id"] != combined["destination_terminal_id"]
            for plan in plans
        ):
            raise HTTPException(409, "Replacement cannot share a common terminal pair.")
        pool = PoolingGroup(
            id=uid("pool"),
            vessel_id=vessel.id,
            cargo_ids=[c.id for c in cargos],
            total_tonnes=merged.weight_tonnes,
            utilization=merged.weight_tonnes / vessel.max_capacity_tonnes,
            solver_status="REVALIDATED_RECOVERY",
        )
        db.add(pool)
        db.flush()
    for reservation in list(
        db.scalars(
            select(ResourceReservation).where(
                ResourceReservation.booking_id.in_(exclusions)
            )
        )
    ):
        db.delete(reservation)
    db.flush()
    results = []
    for member, cargo, plan in zip(members, cargos, plans):
        if combined:
            plan = {
                **plan,
                **{
                    key: combined[key]
                    for key in ["departure", "loading_start", "unloading_start", "eta"]
                },
            }
        results.append(
            approve_recovery(
                db,
                actor,
                member,
                payload,
                commit=False,
                acquire_lock=False,
                exclusions=exclusions,
                plan_override=plan,
                reserve_resources=False,
            )
        )
        if pool:
            member.pool_id = pool.id
            metric = db.scalar(
                select(ImpactMetric).where(ImpactMetric.booking_id == member.id)
            )
            metric.utilization_after = pool.utilization
    if pool:
        reserve_plan(db, members[0], merged, vessel)
    audit(
        db,
        "pool.recovery_approved",
        pool.id if pool else booking.id,
        actor,
        booking_ids=exclusions,
    )
    db.commit()
    return {
        "booking_ids": exclusions,
        "pool_id": pool.id if pool else None,
        "recovered_count": len(members),
        "results": results,
    }
