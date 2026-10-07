import math
from datetime import timedelta
from types import SimpleNamespace
from fastapi import HTTPException
from sqlalchemy import select, text
from backend.auth import cargo_access, GLOBAL_ROLES
from backend.models import *
from backend.repositories.common import uid, require, record, audit
from backend.services.timeutils import dt, utcnow
from backend.services.planning import compare_modes
from feasibility.engine import check_feasibility
from feasibility.cargo_constraints.compatibility import compatible
from feasibility.vessel_constraints.checks import ACTIVE_BOOKING_STATES
from optimization.config import TRUCK_CAPACITY_TONNES, RATES
from optimization.multimodal.costs import coordinates

NEXT_STATES = {
    "CONFIRMED": {"SCHEDULED", "CANCELLED", "REPLANNING", "FAILED"},
    "SCHEDULED": {"LOADING", "CANCELLED", "REPLANNING", "FAILED"},
    "LOADING": {"IN_TRANSIT", "REPLANNING", "FAILED"},
    "IN_TRANSIT": {"UNLOADING", "REPLANNING", "FAILED"},
    "UNLOADING": {"LAST_MILE", "DELIVERED", "REPLANNING", "FAILED"},
    "LAST_MILE": {"DELIVERED", "REPLANNING", "FAILED"},
    "REPLANNING": {"SCHEDULED", "CANCELLED", "FAILED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
    "FAILED": set(),
}
PROGRESS = {
    "CONFIRMED": 0,
    "SCHEDULED": 0.05,
    "LOADING": 0.12,
    "IN_TRANSIT": 0.5,
    "UNLOADING": 0.88,
    "LAST_MILE": 0.96,
    "DELIVERED": 1,
}


def lock_writes(db):
    # SQLite serializes reservation checks and writes, preventing check/write races.
    # PostgreSQL migrations use row locks on cargo and vessel below.
    if db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))


def booking_access(db, actor, booking):
    if actor.role_id in GLOBAL_ROLES:
        return
    if actor.role_id == "control":
        cargo_access(actor, db.get(CargoRequest, booking.cargo_id))
        return
    if booking.organization_id == actor.organization_id:
        return
    if booking.vessel_id:
        vessel = db.get(Vessel, booking.vessel_id)
        if vessel.organization_id == actor.organization_id and actor.role_id in {
            "operator",
            "fleet",
            "captain",
            "maintenance",
        }:
            return
    if actor.role_id == "terminal" and any(
        db.get(Terminal, key).organization_id == actor.organization_id
        for key in [booking.origin_terminal_id, booking.destination_terminal_id]
        if key
    ):
        return
    raise HTTPException(404, "Record not found.")


def booking_risk(cargo, plan):
    slack = (dt(cargo.delivery_deadline) - dt(plan["eta"])).total_seconds() / 3600
    contributions = {
        "reliability": round((1 - plan["reliability"]) * 40, 1),
        "schedule_slack": 25 if slack < 1 else 10 if slack < 3 else 0,
        "cargo_complexity": 15 if cargo.hazardous or cargo.fragile else 0,
        "handoffs": max(0, plan["handoffs"] - 2) * 5,
    }
    score = sum(contributions.values())
    return {
        "level": "HIGH" if score >= 35 else "MEDIUM" if score >= 15 else "LOW",
        "score": score,
        "factors": contributions,
        "slack_hours": round(slack, 2),
        "model": "Transparent deterministic decision support; not predictive ML",
        "weather": "Not connected",
    }


def _active_for_cargo(db, cargo_id):
    return db.scalar(
        select(Booking).where(
            Booking.cargo_id == cargo_id,
            Booking.status.in_(list(ACTIVE_BOOKING_STATES | {"DELIVERED"})),
        )
    )


def create_booking(db, actor, request, commit=True, acquire_lock=True):
    if not request.approved:
        raise HTTPException(422, "Explicit booking approval is required.")
    if acquire_lock:
        lock_writes(db)
    cargo = require(db, CargoRequest, request.cargo_id)
    cargo_access(actor, cargo)
    if db.bind.dialect.name != "sqlite":
        db.execute(
            select(CargoRequest).where(CargoRequest.id == cargo.id).with_for_update()
        )
    cargos = [cargo]
    pool = None
    if request.pool_id:
        pool = require(db, PoolingGroup, request.pool_id)
        if (
            request.mode == "ROAD"
            or pool.vessel_id != request.vessel_id
            or cargo.id not in pool.cargo_ids
        ):
            raise HTTPException(
                422, "Pool must contain this cargo and use the selected vessel."
            )
        cargos = [require(db, CargoRequest, key) for key in pool.cargo_ids]
        for item in cargos:
            cargo_access(actor, item)
        if any(
            not compatible(a, b) for i, a in enumerate(cargos) for b in cargos[i + 1 :]
        ):
            raise HTTPException(409, "The selected pool is no longer compatible.")
    for item in cargos:
        held = db.scalar(select(VoyageMember).join(CargoVoyage).where(
            VoyageMember.cargo_id == item.id, VoyageMember.status == "PROPOSED", CargoVoyage.status == "HELD"))
        if held and dt(db.get(CargoVoyage, held.voyage_id).expires_at) > utcnow():
            raise HTTPException(409, "Cargo has a locked departure proposal; approve its quote and provider jobs.")
        if _active_for_cargo(db, item.id):
            raise HTTPException(
                409, "Cargo already has an active or delivered booking."
            )
    vessel = None
    service = None
    if request.mode != "ROAD":
        if not request.vessel_id:
            raise HTTPException(422, "Water bookings require a vessel.")
        vessel = require(db, Vessel, request.vessel_id)
        if db.bind.dialect.name != "sqlite":
            db.execute(select(Vessel).where(Vessel.id == vessel.id).with_for_update())
    if request.service_id:
        from optimization.scheduled_services.planner import validate_capacity

        service = require(db, ScheduledService, request.service_id)
        if not vessel or vessel.id != service.vessel_id or request.pool_id:
            raise HTTPException(
                422,
                "Scheduled capacity requires the service vessel and an individual cargo.",
            )
        validate_capacity(db, service, cargo, request.contract_id, actor)
    excluded_service_ids = []
    if service:
        for capacity in db.scalars(
            select(ScheduledCapacityBooking).where(
                ScheduledCapacityBooking.service_id == service.id
            )
        ):
            existing = db.get(Booking, capacity.booking_id)
            if existing.status not in {"CANCELLED", "FAILED"}:
                excluded_service_ids.append(existing.id)
                other = db.get(CargoRequest, existing.cargo_id)
                if not compatible(cargo, other):
                    raise HTTPException(409, "Scheduled co-load is incompatible.")
        if cargo.volume_m3 is None:
            raise HTTPException(
                409, "Scheduled capacity booking needs confirmed cargo volume."
            )
        if (
            sum(
                db.get(CargoRequest, db.get(Booking, key).cargo_id).volume_m3 or 0
                for key in excluded_service_ids
            )
            + cargo.volume_m3
            > vessel.max_volume_m3
        ):
            raise HTTPException(409, "Scheduled cargo exceeds vessel volume.")
    from backend.services.demo_state import flood_enabled

    comparisons = [
        compare_modes(
            db,
            item,
            request.vessel_id,
            flood=flood_enabled(db),
            exclude_booking_ids=excluded_service_ids,
        )
        for item in cargos
    ]
    selected = [
        next(p for p in comparison["plans"] if p["mode"] == request.mode)
        for comparison in comparisons
    ]
    if any(not plan["feasible"] for plan in selected):
        reasons = [reason for plan in selected for reason in plan.get("reasons", [])]
        raise HTTPException(
            409, {"message": "Selected mode is infeasible.", "reasons": reasons}
        )
    if any(
        item.budget and plan["total_cost"] > item.budget
        for item, plan in zip(cargos, selected)
    ):
        raise HTTPException(409, "Selected quote exceeds the confirmed cargo budget.")
    combined_plan = None
    if pool:
        merged = SimpleNamespace(**record(cargo))
        from backend.services.terminal_resources import apply_group_requirements

        apply_group_requirements(merged, cargos)
        merged.weight_tonnes = sum(item.weight_tonnes for item in cargos)
        merged.volume_m3 = (
            sum(item.volume_m3 for item in cargos)
            if all(item.volume_m3 is not None for item in cargos)
            else None
        )
        if merged.volume_m3 is None:
            raise HTTPException(
                409, "All pooled cargo volumes must be confirmed before booking."
            )
        merged.ready_time = max((plan["loading_start"] for plan in selected), key=dt)
        terminal_node = db.get(
            WaterwayNode, db.get(Terminal, selected[0]["origin_terminal_id"]).node_id
        )
        merged.origin = terminal_node.name
        merged.origin_coordinates = [terminal_node.latitude, terminal_node.longitude]
        merged.first_mile_required = False
        merged.delivery_deadline = min(
            (item.delivery_deadline for item in cargos), key=dt
        )
        feasibility = check_feasibility(db, merged, vessel)
        if not feasibility["passed"]:
            raise HTTPException(
                409,
                {
                    "message": "Pooled voyage failed revalidation.",
                    "reasons": feasibility["reasons"],
                },
            )
        combined_plan = feasibility["plan"]
        # All loads share the same terminal pair and synchronized departure.
        for item, plan in zip(cargos, selected):
            if (
                plan["origin_terminal_id"] != combined_plan["origin_terminal_id"]
                or plan["destination_terminal_id"]
                != combined_plan["destination_terminal_id"]
            ):
                raise HTTPException(
                    409, "Pool terminal pairs differ; request a common-terminal plan."
                )
            if dt(combined_plan["eta"]) > dt(item.delivery_deadline):
                raise HTTPException(
                    409, "Synchronized pool arrival misses a cargo deadline."
                )
    bookings = []
    for index, (item, plan, comparison) in enumerate(
        zip(cargos, selected, comparisons)
    ):
        if combined_plan:
            plan = {
                **plan,
                **{
                    key: combined_plan[key]
                    for key in ["departure", "loading_start", "unloading_start", "eta"]
                },
            }
        if service:
            from optimization.scheduled_services.planner import service_plan

            plan = service_plan(db, service, item, plan)
            if request.contract_id:
                contract = db.get(CapacityContract, request.contract_id)
                breakdown = {
                    **plan["breakdown"],
                    "water_freight": round(
                        contract.rate_per_tonne * item.weight_tonnes, 2
                    ),
                }
                plan = {
                    **plan,
                    "breakdown": breakdown,
                    "total_cost": round(sum(breakdown.values()), 2),
                    "contract_id": contract.id,
                }
                if item.budget and plan["total_cost"] > item.budget:
                    raise HTTPException(
                        409, "Contract delivered price exceeds confirmed cargo budget."
                    )
        risk = booking_risk(item, plan)
        booking = Booking(
            id=uid("booking"),
            organization_id=item.organization_id,
            cargo_id=item.id,
            vessel_id=request.vessel_id if request.mode != "ROAD" else None,
            availability_id=plan.get("availability_id"),
            origin_terminal_id=plan.get("origin_terminal_id"),
            destination_terminal_id=plan.get("destination_terminal_id"),
            mode=request.mode,
            total_cost=plan["total_cost"],
            cost_breakdown=plan["breakdown"],
            departure=plan["departure"],
            eta=plan["eta"],
            risk=risk,
            plan_snapshot=plan,
            pool_id=request.pool_id,
        )
        db.add(booking)
        db.flush()
        coords = coordinates(item.origin, item.origin_coordinates)
        shipment = Shipment(
            id=uid("shipment"),
            booking_id=booking.id,
            latitude=coords[0],
            longitude=coords[1],
            operational_data={},
        )
        db.add(shipment)
        db.flush()
        db.add(
            TrackingEvent(
                id=uid("event"),
                shipment_id=shipment.id,
                status="CONFIRMED",
                description="Booking approved. Tracking positions are simulated.",
                latitude=coords[0],
                longitude=coords[1],
            )
        )
        if request.mode == "ROAD":
            legs = [("ROAD", item.origin, item.destination)]
        else:
            legs = (
                []
                if not plan.get("first_mile_km")
                else [("ROAD", item.origin, plan["origin_terminal"])]
            ) + [("WATER", plan["origin_terminal"], plan["destination_terminal"])]
            if item.last_mile_required:
                legs.append(("ROAD", plan["destination_terminal"], item.destination))
        for i, (mode, origin, destination) in enumerate(legs):
            db.add(
                ShipmentLeg(
                    id=uid("leg"),
                    shipment_id=shipment.id,
                    mode=mode,
                    origin=origin,
                    destination=destination,
                    sequence=i,
                    assigned_provider=vessel.name if mode == "WATER" else None,
                )
            )
        if request.contract_id:
            if not service:
                raise HTTPException(
                    422, "Contract capacity requires a scheduled service."
                )
            db.add(
                ContractDraw(
                    id=uid("contract-draw"),
                    contract_id=request.contract_id,
                    booking_id=booking.id,
                    service_id=service.id,
                    tonnes=item.weight_tonnes,
                )
            )
        if vessel and (index == 0 or service):
            from backend.services.terminal_resources import reserve_plan

            reserve_cargo = SimpleNamespace(**record(item))
            if pool:
                apply_group_requirements(reserve_cargo, cargos)
                reserve_cargo.weight_tonnes = sum(c.weight_tonnes for c in cargos)
                reserve_cargo.cargo_type = (
                    "construction"
                    if any(c.cargo_type in {"steel", "construction"} for c in cargos)
                    else item.cargo_type
                )
            reserve_plan(
                db, booking, reserve_cargo, vessel, service.id if service else None
            )
        if vessel and index == 0:
            for operation, terminal_id, start_key in [
                ("LOADING", plan["origin_terminal_id"], "loading_start"),
                ("UNLOADING", plan["destination_terminal_id"], "unloading_start"),
            ]:
                start = dt(plan[start_key])
                db.add(
                    TerminalSlot(
                        id=uid("slot"),
                        terminal_id=terminal_id,
                        booking_id=booking.id,
                        starts_at=start.isoformat(),
                        ends_at=(
                            start + timedelta(hours=RATES["handling_hours"])
                        ).isoformat(),
                        operation=operation,
                    )
                )
        road = comparison["plans"][0]
        utilization = (
            sum(c.weight_tonnes for c in cargos) / vessel.max_capacity_tonnes
            if vessel
            else 0
        )
        db.add(
            ImpactMetric(
                id=uid("impact"),
                booking_id=booking.id,
                tonnes_shifted=item.weight_tonnes if vessel else 0,
                road_baseline_cost=road.get("total_cost") or 0,
                chosen_cost=booking.total_cost,
                road_emissions_kg=road.get("emissions_kg", 0),
                chosen_emissions_kg=plan.get("emissions_kg", 0),
                truck_trips_avoided=math.ceil(
                    item.weight_tonnes / TRUCK_CAPACITY_TONNES
                )
                if vessel
                else 0,
                utilization_before=cargo.weight_tonnes / vessel.max_capacity_tonnes
                if vessel
                else 0,
                utilization_after=utilization,
                empty_return_avoided=False,
            )
        )
        invoice = InvoiceRecord(
            id=uid("invoice"),
            booking_id=booking.id,
            total=booking.total_cost,
            line_items=booking.cost_breakdown,
        )
        db.add(invoice)
        db.flush()
        db.add(
            PaymentRecord(
                id=uid("payment"),
                invoice_id=invoice.id,
                amount=booking.total_cost,
                operator_payout=round(
                    booking.cost_breakdown.get("water_freight", 0) * 0.95, 2
                ),
            )
        )
        item.status = "CONFIRMED"
        bookings.append({"booking": record(booking), "shipment": record(shipment)})
        if service:
            from optimization.scheduled_services.planner import stop_pair

            start_stop, end_stop = stop_pair(db, service, item)
            db.add(
                ScheduledCapacityBooking(
                    id=uid("capacity"),
                    service_id=service.id,
                    cargo_id=item.id,
                    booking_id=booking.id,
                    weight_tonnes=item.weight_tonnes,
                    start_sequence=start_stop.sequence,
                    end_sequence=end_stop.sequence,
                )
            )
        # A booked reverse load counts only when an earlier outbound voyage was
        # actually booked on this vessel, rather than when a suggestion exists.
        if vessel:
            from optimization.terminal_selection.planner import node_for

            for previous in db.scalars(
                select(Booking).where(
                    Booking.vessel_id == vessel.id, Booking.id != booking.id
                )
            ):
                previous_cargo = db.get(CargoRequest, previous.cargo_id)
                if (
                    previous.status not in {"CANCELLED", "FAILED"}
                    and dt(previous.eta) <= dt(booking.departure)
                    and node_for(previous_cargo.origin) == node_for(item.destination)
                    and node_for(previous_cargo.destination) == node_for(item.origin)
                ):
                    metric = db.scalar(
                        select(ImpactMetric).where(
                            ImpactMetric.booking_id == previous.id
                        )
                    )
                    if metric:
                        metric.empty_return_avoided = True
        audit(
            db,
            "booking.created",
            booking.id,
            actor,
            cargo_id=item.id,
            mode=request.mode,
            shipment_id=shipment.id,
        )
    if commit:
        db.commit()
    return {
        "bookings": bookings,
        "booking": bookings[0]["booking"],
        "shipment": bookings[0]["shipment"],
        "manifest_url": f"/api/bookings/{bookings[0]['booking']['id']}/documents/manifest",
    }


def transition(db, actor, shipment, new_state):
    booking = require(db, Booking, shipment.booking_id)
    booking_access(db, actor, booking)
    if db.scalar(select(VoyageMember).where(VoyageMember.booking_id == shipment.booking_id)):
        raise HTTPException(409, "Use Cargo Lines shared milestones and individual receipt actions.")
    if new_state not in NEXT_STATES.get(shipment.status, set()):
        raise HTTPException(409, f"Cannot transition {shipment.status} → {new_state}.")
    if (
        new_state == "DELIVERED"
        and require(db, CargoRequest, booking.cargo_id).last_mile_required
        and shipment.status == "UNLOADING"
    ):
        raise HTTPException(
            409, "Required last-mile leg must be completed before delivery."
        )
    cargo = db.get(CargoRequest, booking.cargo_id)
    if (
        new_state == "DELIVERED"
        and shipment.operational_data.get("pod_required")
        and not shipment.operational_data.get("pod_verified")
    ):
        raise HTTPException(
            409, "Receiver must verify the active delivery challenge before delivery."
        )
    if new_state == "IN_TRANSIT" and cargo.volume_m3 is None:
        raise HTTPException(409, "Verify cargo volume before departure.")
    shipment.status = booking.status = cargo.status = new_state
    shipment.progress = PROGRESS.get(new_state, shipment.progress)
    origin = coordinates(cargo.origin, cargo.origin_coordinates)
    destination = coordinates(cargo.destination, cargo.destination_coordinates)
    waypoints = [origin]
    for node_id in booking.plan_snapshot.get("route", {}).get("nodes", []):
        node = db.get(WaterwayNode, node_id)
        point = (node.latitude, node.longitude)
        if point != waypoints[-1]:
            waypoints.append(point)
    if waypoints[-1] != destination:
        waypoints.append(destination)
    from optimization.multimodal.costs import road_distance

    lengths = [
        road_distance(first, second) for first, second in zip(waypoints, waypoints[1:])
    ]
    remaining = sum(lengths) * shipment.progress
    position = destination
    for index, length in enumerate(lengths):
        if remaining <= length and length:
            ratio = remaining / length
            first, second = waypoints[index : index + 2]
            position = (
                first[0] + (second[0] - first[0]) * ratio,
                first[1] + (second[1] - first[1]) * ratio,
            )
            break
        remaining -= length
    shipment.latitude, shipment.longitude = position
    if booking.vessel_id:
        vessel = db.get(Vessel, booking.vessel_id)
        vessel.state = {
            "LOADING": "LOADING",
            "IN_TRANSIT": "SAILING",
            "UNLOADING": "UNLOADING",
        }.get(new_state, "AVAILABLE")
    db.add(
        TrackingEvent(
            id=uid("event"),
            shipment_id=shipment.id,
            status=new_state,
            description=f"Shipment moved to {new_state.replace('_', ' ').lower()}. Position simulated.",
            latitude=shipment.latitude,
            longitude=shipment.longitude,
        )
    )
    audit(db, "shipment.status_changed", shipment.id, actor, status=new_state)
    db.commit()
    return record(shipment)
