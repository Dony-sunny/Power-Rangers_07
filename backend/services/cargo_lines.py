"""Local, serialized Cargo Lines reservations. Provider responses are simulated."""
import hashlib
import json
from decimal import Decimal
from datetime import timedelta
from types import SimpleNamespace
from fastapi import HTTPException
from sqlalchemy import select
from backend.auth import cargo_access, coordinated_orgs
from backend.models import *
from backend.repositories.common import uid, require, record, audit
from backend.services.timeutils import dt, utcnow, overlaps
from backend.services.bookings import lock_writes, _active_for_cargo, booking_risk
from backend.services.line_planning import build_plan, loaded_cargo
from backend.services.terminal_resources import choose_resources, apply_group_requirements, peak_quantity, reservations
from feasibility.vessel_constraints.checks import ACTIVE_BOOKING_STATES
from optimization.multimodal.costs import coordinates, road_plan
from optimization.multimodal.trip_costs import TERMS, minor, rupees, sailing_economics, allocate

DEAD_VOYAGES = {"CANCELLED", "DECLINED", "EXPIRED", "DISRUPTED", "COMPLETED"}


def members(db, voyage):
    rows = list(db.scalars(select(VoyageMember).where(VoyageMember.voyage_id == voyage.id)))
    order = {p["cargo_id"]: i for i, p in enumerate(voyage.plan["members"])}
    return sorted(rows, key=lambda m: order[m.cargo_id])


def jobs(db, voyage):
    return list(db.scalars(select(ProviderJob).where(ProviderJob.voyage_id == voyage.id).order_by(ProviderJob.id)))


def revision(db, cargo):
    data = vars(loaded_cargo(db, cargo)).copy()
    data.pop("status", None)
    def canonical(value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(Decimal(str(value)).normalize())
        if isinstance(value, dict):
            return {key: canonical(field) for key, field in value.items()}
        if isinstance(value, (list, tuple)):
            return [canonical(field) for field in value]
        return value
    return hashlib.sha256(json.dumps(canonical(data), sort_keys=True, default=str).encode()).hexdigest()


def coordinate(actor, voyage):
    if actor.role_id != "control" or actor.organization_id != voyage.coordinator_org_id:
        raise HTTPException(404, "Departure not found in your coordination queue.")


def view_access(db, actor, voyage):
    if actor.role_id in {"admin", "government", "network", "compliance"}:
        return
    if actor.role_id == "control" and actor.organization_id == voyage.coordinator_org_id:
        return
    if actor.role_id in {"operator", "fleet", "captain", "maintenance"} and voyage.vessel_id and db.get(Vessel, voyage.vessel_id).organization_id == actor.organization_id:
        return
    if actor.role_id in {"shipper", "dispatch", "warehouse", "receiver", "finance"} and any(db.get(CargoRequest, m.cargo_id).organization_id == actor.organization_id for m in members(db, voyage)):
        return
    if actor.role_id == "terminal" and any(job.provider_org_id == actor.organization_id for job in jobs(db, voyage)):
        return
    raise HTTPException(404, "Departure not found.")


def can_record_milestone(db, actor, voyage, status):
    if actor.role_id == "control":
        return actor.organization_id == voyage.coordinator_org_id
    if actor.role_id in {"operator", "fleet", "captain"}:
        return db.get(Vessel, voyage.vessel_id).organization_id == actor.organization_id
    if actor.role_id == "dispatch":
        active = [m for m in members(db, voyage) if m.status not in {"CANCELLED", "DELIVERED"}]
        return bool(active) and all(db.get(CargoRequest, m.cargo_id).organization_id == actor.organization_id for m in active)
    if actor.role_id == "terminal" and status in {"LOADING", "UNLOADING"}:
        operation = "LOAD" if status == "LOADING" else "UNLOAD"
        return any(job.provider_org_id == actor.organization_id and job.kind.startswith(operation + "_") for job in jobs(db, voyage))
    return False


def release(db, voyage, state):
    voyage.status = state
    for job in jobs(db, voyage):
        if job.status in {"PENDING", "ACCEPTED"}:
            job.status = "RELEASED"
    for member in members(db, voyage):
        if member.status == "PROPOSED":
            member.status = state


def expire(db):
    for voyage in db.scalars(select(CargoVoyage).where(CargoVoyage.status == "HELD")):
        if utcnow() >= min(dt(voyage.expires_at), dt(voyage.cutoff)):
            release(db, voyage, "EXPIRED")
            for job in jobs(db, voyage):
                if job.status == "RELEASED":
                    job.status = "EXPIRED"


def held(db, voyage):
    expire(db)
    if voyage.status != "HELD":
        # Preserve expiry/release evidence even when this command is rejected.
        db.commit()
        raise HTTPException(409, f"Departure is {voyage.status.lower()}; request a new quote.")


def active_job(db, job):
    voyage = db.get(CargoVoyage, job.voyage_id)
    return job.status in {"PENDING", "ACCEPTED"} and voyage.status not in DEAD_VOYAGES and (voyage.status != "HELD" or utcnow() < min(dt(voyage.expires_at), dt(voyage.cutoff)))


def allocate_jobs(db, voyage, cargos):
    plan = voyage.plan
    merged = SimpleNamespace(**vars(loaded_cargo(db, cargos[0])))
    merged.weight_tonnes = plan["weight_tonnes"]
    apply_group_requirements(merged, cargos)
    merged.needs_crane = plan["required_crane"]
    merged.needs_forklift = plan["required_forklift"]
    vessel = db.get(Vessel, voyage.vessel_id)
    for terminal_id, start, end, operation in [
        (plan["origin_terminal_id"], plan["loading_start"], plan["departure"], "LOAD"),
        (plan["destination_terminal_id"], plan["unloading_start"], plan["water_end"], "UNLOAD"),
    ]:
        chosen, conflicts = choose_resources(db, terminal_id, merged, vessel, start, end, [f"voyage:{voyage.id}"])
        if conflicts:
            raise HTTPException(409, {"message": "Handling resource allocation failed.", "reasons": conflicts})
        for resource, quantity in chosen:
            db.add(ProviderJob(id=uid("job"), voyage_id=voyage.id, cargo_id=None,
                provider_org_id=db.get(Terminal, terminal_id).organization_id,
                terminal_resource_id=resource.id, truck_resource_id=None, kind=f"{operation}_{resource.kind}",
                quantity=quantity, starts_at=start, ends_at=end, expires_at=voyage.expires_at))
    db.flush()
    for cargo in cargos:
        item = loaded_cargo(db, cargo)
        member_plan = next(p for p in plan["members"] if p["cargo_id"] == cargo.id)
        for kind, count, start, end in [
            ("PICKUP_TRUCK", member_plan["first_mile_trips"], member_plan["pickup_start"], plan["departure"]),
            ("DELIVERY_TRUCK", member_plan["last_mile_trips"], plan["water_end"], (dt(member_plan["eta"]) + timedelta(minutes=15)).isoformat()),
        ]:
            for _ in range(count):
                selected = None
                for truck in db.scalars(select(TruckResource).where(TruckResource.active == True).order_by(TruckResource.id)):
                    if (truck.payload_tonnes < TERMS["payload_tonnes"] or truck.volume_m3 < TERMS["truck_volume_m3"] or
                        truck.pieces_per_trip < TERMS["pieces_per_trip"] or (item.cargo_type not in truck.cargo_categories and "general" not in truck.cargo_categories) or item.hazardous or item.temperature_control_required or
                        item.heaviest_piece_tonnes > truck.payload_tonnes or item.unit_length_m > truck.unit_length_m or item.unit_width_m > truck.unit_width_m or item.unit_height_m > truck.unit_height_m):
                        continue
                    conflicts = any(active_job(db, job) and overlaps(start, end, job.starts_at, job.ends_at) for job in db.scalars(select(ProviderJob).where(ProviderJob.truck_resource_id == truck.id)))
                    if not conflicts:
                        selected = truck
                        break
                if not selected:
                    reason = "All matching trucks have schedule conflicts for this time window."
                    if item.heaviest_piece_tonnes > 20:
                        reason = f"Heaviest piece ({item.heaviest_piece_tonnes} t) exceeds truck payload capacity (20 t)."
                    elif item.unit_length_m > 6 or item.unit_width_m > 2.4 or item.unit_height_m > 2.5:
                        reason = f"Unit dimensions ({item.unit_length_m}m × {item.unit_width_m}m × {item.unit_height_m}m) exceed truck bed limit (6m × 2.4m × 2.5m)."
                    elif item.hazardous or item.temperature_control_required:
                        reason = "Hazardous or temperature-controlled goods are not supported by standard demo trucks."
                    elif not any(item.cargo_type in t.cargo_categories or "general" in t.cargo_categories for t in db.scalars(select(TruckResource))):
                        reason = f"Cargo category '{item.cargo_type}' is not supported by available trucks."
                    raise HTTPException(409, f"A required truck has no compatible, free resource/time assignment. {reason}")
                db.add(ProviderJob(id=uid("job"), voyage_id=voyage.id, cargo_id=cargo.id, provider_org_id=selected.organization_id,
                    terminal_resource_id=None, truck_resource_id=selected.id, kind=kind, quantity=1, starts_at=start, ends_at=end, expires_at=voyage.expires_at))
                db.flush()


def propose(db, actor, cargo_ids, vessel_id, parent_id=None, not_before=None, availability_id=None):
    lock_writes(db)
    expire(db)
    if actor.role_id not in {"shipper", "control"}:
        raise HTTPException(403, "Only cargo owners and entrusted coordinators propose departures.")
    cargos = [require(db, CargoRequest, key) for key in cargo_ids]
    for cargo in cargos:
        cargo_access(actor, cargo)
        if actor.role_id == "shipper" and cargo.organization_id != actor.organization_id:
            raise HTTPException(404, "Cargo not found.")
        if _active_for_cargo(db, cargo.id):
            raise HTTPException(409, "Cargo already has an active or delivered booking.")
        for member in db.scalars(select(VoyageMember).where(VoyageMember.cargo_id == cargo.id, VoyageMember.status == "PROPOSED")):
            if db.get(CargoVoyage, member.voyage_id).status == "HELD":
                raise HTTPException(409, "Cargo already has a held quote; cancel that proposal first.")
    coordinator_org = actor.organization_id if actor.role_id == "control" else None
    if not coordinator_org:
        grants = list(db.scalars(select(CoordinationGrant).where(CoordinationGrant.owner_org_id == actor.organization_id)))
        if not grants:
            raise HTTPException(409, "Entrust a coordinator before requesting door-to-door service.")
        coordinator_org = grants[0].coordinator_org_id
    dispatcher = db.scalar(select(User).where(User.role_id == "control", User.organization_id == coordinator_org))
    if not dispatcher:
        raise HTTPException(409, "No service-owner dispatcher is available.")
    plan = build_plan(db, cargos, require(db, Vessel, vessel_id), not_before=not_before, pinned_availability_id=availability_id)
    cutoff = dt(plan["loading_start"]) - timedelta(minutes=30)
    expires = min(utcnow() + timedelta(minutes=20), cutoff)
    if expires <= utcnow():
        raise HTTPException(409, "Confirmation cutoff has passed; choose another departure.")
    voyage = CargoVoyage(id=uid("voyage"), coordinator_org_id=coordinator_org, dispatcher_id=dispatcher.id,
        vessel_id=vessel_id, plan=plan, expires_at=expires.isoformat(), cutoff=cutoff.isoformat(), parent_id=parent_id)
    db.add(voyage)
    db.flush()
    allocate_jobs(db, voyage, cargos)
    for cargo in cargos:
        snapshot = next(p for p in plan["members"] if p["cargo_id"] == cargo.id)
        snapshot = {**snapshot, "resource_plan": resource_snapshot(db, voyage, cargo.id)}
        quote = LineQuote(id=uid("quote"), voyage_id=voyage.id, cargo_id=cargo.id, organization_id=cargo.organization_id,
            cargo_revision=revision(db, cargo), total_minor=snapshot["total_minor"], snapshot=snapshot, expires_at=expires.isoformat())
        db.add(quote)
        db.flush()
        db.add(VoyageMember(id=uid("member"), voyage_id=voyage.id, quote_id=quote.id, cargo_id=cargo.id))
    db.flush()
    audit(db, "line.proposed", voyage.id, actor, quote_ids=[m.quote_id for m in members(db, voyage)], source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def resource_snapshot(db, voyage, cargo_id):
    return [{key: getattr(job, key) for key in ["id", "kind", "cargo_id", "provider_org_id", "terminal_resource_id", "truck_resource_id", "quantity", "starts_at", "ends_at", "source"]}
            for job in jobs(db, voyage) if job.cargo_id is None or job.cargo_id == cargo_id]


def approve_quote(db, actor, quote_id):
    lock_writes(db)
    quote = require(db, LineQuote, quote_id)
    if actor.role_id != "shipper" or quote.organization_id != actor.organization_id:
        raise HTTPException(404, "Quote not found.")
    voyage = db.get(CargoVoyage, quote.voyage_id)
    held(db, voyage)
    if revision(db, db.get(CargoRequest, quote.cargo_id)) != quote.cargo_revision:
        raise HTTPException(409, "Cargo changed; request and accept a new quote version.")
    if not db.scalar(select(QuoteAcceptance).where(QuoteAcceptance.quote_id == quote.id)):
        db.add(QuoteAcceptance(id=uid("acceptance"), quote_id=quote.id, actor_id=actor.id))
        audit(db, "line.quote_accepted", quote.id, actor, total_minor=quote.total_minor)
    db.commit()
    return serialize(db, actor, voyage)


def revalidate(db, voyage):
    cargos = [db.get(CargoRequest, m.cargo_id) for m in members(db, voyage) if m.status == "PROPOSED"]
    for member in members(db, voyage):
        quote = db.get(LineQuote, member.quote_id)
        if revision(db, db.get(CargoRequest, member.cargo_id)) != quote.cargo_revision or _active_for_cargo(db, member.cargo_id):
            raise HTTPException(409, "Cargo revision/booking changed; explicit new quote approval is required.")
        if quote.snapshot.get("resource_plan") != resource_snapshot(db, voyage, member.cargo_id):
            raise HTTPException(409, "Quoted truck/terminal assignments changed; approve a new resource plan.")
    pinned = {db.get(TerminalRateCard, key).terminal_id: key for key in voyage.plan["rate_card_ids"]}
    current = build_plan(db, cargos, require(db, Vessel, voyage.vessel_id), [f"voyage:{voyage.id}"], pinned, voyage.plan["availability_id"], voyage.plan.get("not_before"))
    if current != voyage.plan:
        raise HTTPException(409, "Price, departure or resources changed; request a new departure and quote approval.")
    for job in jobs(db, voyage):
        if job.truck_resource_id:
            truck = db.get(TruckResource, job.truck_resource_id)
            if not truck.active or truck.payload_tonnes < 20 or truck.volume_m3 < 60 or truck.pieces_per_trip < 2000:
                raise HTTPException(409, "An accepted truck's usable capacity changed.")
            cargo = loaded_cargo(db, db.get(CargoRequest, job.cargo_id))
            if (cargo.cargo_type not in truck.cargo_categories and "general" not in truck.cargo_categories) or cargo.unit_length_m > truck.unit_length_m or cargo.unit_width_m > truck.unit_width_m or cargo.unit_height_m > truck.unit_height_m:
                raise HTTPException(409, "Assigned truck no longer fits the reviewed load.")
            if any(other.id != job.id and other.voyage_id != voyage.id and active_job(db, other) and overlaps(job.starts_at, job.ends_at, other.starts_at, other.ends_at) for other in db.scalars(select(ProviderJob).where(ProviderJob.truck_resource_id == truck.id))):
                raise HTTPException(409, "Assigned truck has a conflicting reservation.")
        elif job.terminal_resource_id:
            resource = db.get(TerminalResource, job.terminal_resource_id)
            if not resource.active or peak_quantity(reservations(db, resource, [f"voyage:{voyage.id}"]), job.starts_at, job.ends_at) + job.quantity > resource.capacity:
                raise HTTPException(409, "Accepted terminal resource has changed or conflicts.")
    return current


def operator_response(db, actor, voyage_id, version, accept, acknowledge_shortfall=False):
    lock_writes(db)
    voyage = require(db, CargoVoyage, voyage_id)
    if actor.role_id != "operator" or db.get(Vessel, voyage.vessel_id).organization_id != actor.organization_id:
        raise HTTPException(404, "Departure not found for your vessel.")
    held(db, voyage)
    if version != voyage.version:
        raise HTTPException(409, "Review the latest combined load before accepting.")
    revalidate(db, voyage)
    if accept:
        if not all(db.scalar(select(QuoteAcceptance).where(QuoteAcceptance.quote_id == m.quote_id)) for m in members(db, voyage)):
            raise HTTPException(409, "Cargo owners must accept their revenue commitments first.")
        if not voyage.plan["economics"]["covers_modeled_costs"] and not acknowledge_shortfall:
            raise HTTPException(409, "Estimated sailing costs exceed approved revenue. Review and acknowledge the shortfall to accept this departure.")
        voyage.operator_accepted_version, voyage.operator_id = version, actor.id
    else:
        release(db, voyage, "DECLINED")
    audit(db, "line.operator_response", voyage.id, actor, version=version, accepted=accept, acknowledged_shortfall=bool(accept and acknowledge_shortfall), source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def job_response(db, actor, job_id, status):
    lock_writes(db)
    job = require(db, ProviderJob, job_id)
    voyage = db.get(CargoVoyage, job.voyage_id)
    coordinate(actor, voyage)
    held(db, voyage)
    if job.status == status:
        return serialize(db, actor, voyage)
    if job.status != "PENDING":
        raise HTTPException(409, "Job already has a provider response.")
    job.status, job.responded_at = status, utcnow().isoformat()
    job.provider_reference = f"SIM-{job.id}"
    if status == "DECLINED":
        release(db, voyage, "DECLINED")
    audit(db, "line.provider_response", job.id, actor, status=status, source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def confirm(db, actor, voyage_id):
    lock_writes(db)
    voyage = require(db, CargoVoyage, voyage_id)
    view_access(db, actor, voyage)
    if actor.role_id not in {"shipper", "control"}:
        raise HTTPException(403, "Cargo owner or coordinator confirmation required.")
    if voyage.status == "CONFIRMED":
        return serialize(db, actor, voyage)  # Repeated local submission is idempotent.
    held(db, voyage)
    if not all(db.scalar(select(QuoteAcceptance).where(QuoteAcceptance.quote_id == m.quote_id)) for m in members(db, voyage)):
        raise HTTPException(409, "Every cargo owner must approve the exact quote version.")
    if voyage.operator_accepted_version != voyage.version or any(job.status != "ACCEPTED" for job in jobs(db, voyage)):
        raise HTTPException(409, "Operator and every required truck/handling job must accept first.")
    revalidate(db, voyage)
    all_members = members(db, voyage)
    operator_allowances = allocate(voyage.plan["economics"]["water_operating_minor"], [db.get(CargoRequest, m.cargo_id).weight_tonnes for m in all_members])
    for member, operator_allowance in zip(all_members, operator_allowances):
        cargo, quote = db.get(CargoRequest, member.cargo_id), db.get(LineQuote, member.quote_id)
        plan = quote.snapshot
        booking = Booking(id=uid("booking"), organization_id=cargo.organization_id, cargo_id=cargo.id,
            vessel_id=voyage.vessel_id, availability_id=plan["availability_id"], origin_terminal_id=plan["origin_terminal_id"], destination_terminal_id=plan["destination_terminal_id"],
            mode=plan["mode"], total_cost=rupees(quote.total_minor), cost_breakdown=plan["breakdown"], departure=plan["departure"], eta=plan["eta"],
            risk=booking_risk(cargo, plan), plan_snapshot={**plan, "voyage_id": voyage.id, "quote_id": quote.id, "provider_source": "SIMULATED"}, pool_id=None)
        db.add(booking)
        db.flush()
        position = coordinates(cargo.origin, cargo.origin_coordinates)
        shipment = Shipment(id=uid("shipment"), booking_id=booking.id, latitude=position[0], longitude=position[1], operational_data={"service_owner_org_id": voyage.coordinator_org_id, "dispatcher_id": voyage.dispatcher_id})
        db.add(shipment)
        db.flush()
        db.add(TrackingEvent(id=uid("event"), shipment_id=shipment.id, status="CONFIRMED", description="Exact quote and every provider accepted; local simulated commitment.", latitude=position[0], longitude=position[1], simulated=True))
        legs = []
        if cargo.first_mile_required:
            legs.append(("ROAD", cargo.origin, plan["origin_terminal"], "PICKUP_TRUCK"))
        legs.append(("WATER", plan["origin_terminal"], plan["destination_terminal"], "VESSEL"))
        if cargo.last_mile_required:
            legs.append(("ROAD", plan["destination_terminal"], cargo.destination, "DELIVERY_TRUCK"))
        for sequence, (mode, origin, destination, kind) in enumerate(legs):
            assigned = [j.truck_resource_id for j in jobs(db, voyage) if j.cargo_id == cargo.id and j.kind == kind]
            db.add(ShipmentLeg(id=uid("leg"), shipment_id=shipment.id, mode=mode, origin=origin, destination=destination, sequence=sequence,
                assigned_provider=voyage.vessel_id if kind == "VESSEL" else ", ".join(assigned)))
        invoice = InvoiceRecord(id=uid("invoice"), booking_id=booking.id, total=rupees(quote.total_minor), line_items=plan["breakdown"])
        db.add(invoice)
        db.flush()
        db.add(PaymentRecord(id=uid("payment"), invoice_id=invoice.id, amount=invoice.total, operator_payout=rupees(operator_allowance)))
        road = plan["road_baseline"]
        db.add(ImpactMetric(id=uid("impact"), booking_id=booking.id, tonnes_shifted=cargo.weight_tonnes, road_baseline_cost=road["total_cost"], chosen_cost=booking.total_cost,
            road_emissions_kg=road["emissions_kg"], chosen_emissions_kg=plan["emissions_kg"], truck_trips_avoided=road["truck_trips"], utilization_before=cargo.weight_tonnes / db.get(Vessel, voyage.vessel_id).max_capacity_tonnes,
            utilization_after=voyage.plan["utilization"], empty_return_avoided=False))
        member.booking_id, member.status, cargo.status = booking.id, "CONFIRMED", "CONFIRMED"
    voyage.status = "CONFIRMED"
    audit(db, "line.bundle_confirmed", voyage.id, actor, source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def cancel(db, actor, voyage_id, cargo_id=None):
    lock_writes(db)
    voyage = require(db, CargoVoyage, voyage_id)
    view_access(db, actor, voyage)
    if actor.role_id not in {"shipper", "control"}:
        raise HTTPException(403, "Cargo owner or coordinator cancellation required.")
    if voyage.status == "HELD":
        if actor.role_id == "shipper" and any(db.get(CargoRequest, m.cargo_id).organization_id != actor.organization_id for m in members(db, voyage)):
            raise HTTPException(403, "Ask the coordinator to replace this shared proposal.")
        release(db, voyage, "CANCELLED")
    elif voyage.status == "CONFIRMED" and cargo_id:
        member = next((m for m in members(db, voyage) if m.cargo_id == cargo_id), None)
        if not member:
            raise HTTPException(404, "Cargo is not on this departure.")
        cargo = db.get(CargoRequest, cargo_id)
        cargo_access(actor, cargo)
        booking = db.get(Booking, member.booking_id)
        if booking.status not in {"CONFIRMED", "SCHEDULED"}:
            raise HTTPException(409, "Cancellation is supported only before pickup/loading.")
        member.status = booking.status = cargo.status = "CANCELLED"
        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
        shipment.status = "CANCELLED"
        db.add(TrackingEvent(id=uid("event"), shipment_id=shipment.id, status="CANCELLED", description="Owner/coordinator cancelled before pickup; shared jobs retained for remaining loads.", latitude=shipment.latitude, longitude=shipment.longitude))
        invoice = db.scalar(select(InvoiceRecord).where(InvoiceRecord.booking_id == booking.id))
        invoice.status = "VOID"
        for job in jobs(db, voyage):
            if job.cargo_id == cargo_id:
                job.status = "RELEASED"
        if not any(m.status not in {"CANCELLED", "DELIVERED"} for m in members(db, voyage)):
            release(db, voyage, "CANCELLED")
    else:
        raise HTTPException(409, "Select an active cargo or cancel a held proposal.")
    audit(db, "line.cancelled", voyage.id, actor, cargo_id=cargo_id)
    db.commit()
    return serialize(db, actor, voyage)


def serialize(db, actor, voyage):
    view_access(db, actor, voyage)
    all_members = members(db, voyage)
    active = [m for m in all_members if m.status not in {"CANCELLED", "DECLINED", "EXPIRED", "DISRUPTED"}]
    weight = sum(db.get(CargoRequest, m.cargo_id).weight_tonnes for m in active)
    accepted = [m for m in active if db.scalar(select(QuoteAcceptance).where(QuoteAcceptance.quote_id == m.quote_id))]
    water_revenue = sum(sum(db.get(LineQuote, m.quote_id).snapshot["breakdown_minor"][key] for key in ["sailing_fixed", "water_freight"]) for m in accepted)
    economics = sailing_economics(weight, voyage.plan["route"]["distance_km"], db.get(Vessel, voyage.vessel_id).rate_per_tonne_km, water_revenue, voyage.plan.get("tariff", TERMS))
    water_operating = economics["operating_cost_minor"]
    shared_keys = {"sailing_fixed", "water_freight", "origin_handling_setup", "destination_handling_setup"}
    shared_terminal_payable = sum(sum(db.get(LineQuote, m.quote_id).snapshot["breakdown_minor"][key] for key in ["origin_handling_setup", "destination_handling_setup"]) for m in all_members)
    variable_pass_through = sum(sum(value for key, value in db.get(LineQuote, m.quote_id).snapshot["breakdown_minor"].items() if key not in shared_keys) for m in active)
    pass_through = variable_pass_through + shared_terminal_payable
    total_revenue = sum(db.get(LineQuote, m.quote_id).total_minor for m in accepted)
    total_cost = water_operating + pass_through
    economics.update({"water_revenue_minor": water_revenue, "water_operating_minor": water_operating, "provider_pass_through_minor": pass_through,
        "revenue_minor": total_revenue, "operating_cost_minor": total_cost, "contribution_minor": total_revenue - total_cost,
        "covers_modeled_costs": total_revenue >= total_cost, "basis": voyage.plan["economics"]["basis"]})
    result = {"id": voyage.id, "version": voyage.version, "status": voyage.status, "vessel_id": voyage.vessel_id,
        "vessel_name": db.get(Vessel, voyage.vessel_id).name, "departure": voyage.plan["departure"], "loading_start": voyage.plan["loading_start"], "water_end": voyage.plan["water_end"],
        "expires_at": voyage.expires_at, "cutoff": voyage.cutoff, "operator_accepted": voyage.operator_accepted_version == voyage.version,
        "service_owner": db.get(Organization, voyage.coordinator_org_id).name, "dispatcher_id": voyage.dispatcher_id,
        "commitment_policy": voyage.plan["commitment_policy"], "weight_tonnes": weight, "utilization": weight / db.get(Vessel, voyage.vessel_id).max_capacity_tonnes,
        "source": "SIMULATED", "members": [], "jobs": [], "parent_id": voyage.parent_id}
    if actor.role_id in {"control", "operator", "admin"}:
        result["projected_economics"] = voyage.plan["economics"]
        result["accepted_economics"] = economics
        result["viability_warning"] = voyage.status == "CONFIRMED" and not economics["covers_modeled_costs"]
    for member in all_members:
        cargo = db.get(CargoRequest, member.cargo_id)
        own = cargo.organization_id == actor.organization_id
        if actor.role_id in {"shipper", "dispatch", "warehouse", "receiver", "finance"} and not own:
            continue
        quote = db.get(LineQuote, member.quote_id)
        booking = db.get(Booking, member.booking_id) if member.booking_id else None
        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id)) if booking else None
        row = {"cargo_id": cargo.id, "cargo_type": cargo.cargo_type, "weight_tonnes": cargo.weight_tonnes, "origin": cargo.origin, "destination": cargo.destination,
            "eta": quote.snapshot["eta"], "status": booking.status if booking else member.status, "accepted": bool(db.scalar(select(QuoteAcceptance).where(QuoteAcceptance.quote_id == quote.id))),
            "booking_id": member.booking_id, "shipment_id": shipment.id if shipment else None, "receipt": member.receipt,
            "delivery_verification": {"required": bool(shipment and shipment.operational_data.get("pod_required")), "verified": bool(shipment and shipment.operational_data.get("pod_verified"))}}
        if actor.role_id in {"control", "admin"} or own and actor.role_id in {"shipper", "finance"}:
            row["quote"] = {**record(quote), "total_cost": rupees(quote.total_minor)}
            if booking:
                row["invoice"] = record(db.scalar(select(InvoiceRecord).where(InvoiceRecord.booking_id == booking.id)))
        result["members"].append(row)
    visible_cargos = {m["cargo_id"] for m in result["members"]}
    for job in jobs(db, voyage):
        if actor.role_id not in {"shipper", "dispatch", "warehouse", "receiver", "finance"} or job.cargo_id is None or job.cargo_id in visible_cargos:
            row = record(job)
            if actor.role_id not in {"control", "operator", "admin", "terminal"}:
                row = {key: row[key] for key in ["id", "kind", "status", "source", "cargo_id", "starts_at", "ends_at"]}
            result["jobs"].append(row)
    quotes_ready = all(db.scalar(select(QuoteAcceptance).where(QuoteAcceptance.quote_id == m.quote_id)) for m in all_members)
    all_jobs = jobs(db, voyage)
    result["owners_ready"] = quotes_ready
    result["providers_ready"] = all(j.status == "ACCEPTED" for j in all_jobs)
    result["accepted_job_count"] = sum(j.status == "ACCEPTED" for j in all_jobs)
    result["job_count"] = len(all_jobs)
    result["next_action_owner"] = ("None" if voyage.status in DEAD_VOYAGES else "Cargo owner" if not quotes_ready else "Boat operator" if not result["operator_accepted"] else "Logistics coordinator")
    closed_actions = {
        "COMPLETED": "Delivery complete. All cargo receipts recorded.",
        "EXPIRED": "Quote expired. Choose a boat and request a new quote.",
        "DECLINED": "Departure declined. Choose a boat and request a new quote.",
        "CANCELLED": "Departure cancelled. Its unused reservations were released.",
        "DISRUPTED": "Choose a replacement boat and request fresh quotes.",
    }
    result["next_action"] = (closed_actions[voyage.status] if voyage.status in DEAD_VOYAGES else "Approve cargo quotes" if not quotes_ready else "Operator accepts departure" if not result["operator_accepted"] else "Coordinator obtains provider responses" if any(j.status != "ACCEPTED" for j in all_jobs) else "Confirm delivery bundle" if voyage.status == "HELD" else "Coordinator records shipment milestones and receipts")
    result["allowed_milestones"] = [status for status in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"] if can_record_milestone(db, actor, voyage, status)]
    result["can_receive"] = actor.role_id == "control" and actor.organization_id == voyage.coordinator_org_id or actor.role_id == "receiver"
    return result


def milestones(db, actor, voyage_id, status):
    lock_writes(db)
    voyage = require(db, CargoVoyage, voyage_id)
    view_access(db, actor, voyage)
    if not can_record_milestone(db, actor, voyage, status):
        raise HTTPException(403, "Your operational role cannot record this shared milestone.")
    if voyage.status != "CONFIRMED":
        raise HTTPException(409, "Only a confirmed bundle can execute milestones.")
    sequence = ["CONFIRMED", "SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"]
    active = [m for m in members(db, voyage) if m.status not in {"CANCELLED", "DELIVERED"}]
    if status not in sequence[1:] or not active:
        raise HTTPException(422, "Choose the next shared voyage milestone.")
    for member in active:
        booking = db.get(Booking, member.booking_id)
        if sequence.index(status) != sequence.index(booking.status) + 1:
            raise HTTPException(409, "Complete shared milestones in order.")
    # These are local demo milestones. Never present the map as live GPS.
    progress = {"SCHEDULED": .05, "LOADING": .12, "IN_TRANSIT": .5, "UNLOADING": .88}
    for member in active:
        booking, cargo = db.get(Booking, member.booking_id), db.get(CargoRequest, member.cargo_id)
        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
        booking.status = cargo.status = member.status = shipment.status = status
        shipment.progress = progress[status]
        db.add(TrackingEvent(id=uid("event"), shipment_id=shipment.id, status=status, description=f"{actor.role_id} recorded shared milestone; position and execution are simulated.", latitude=shipment.latitude, longitude=shipment.longitude, simulated=True))
    db.get(Vessel, voyage.vessel_id).state = "IN_TRANSIT" if status == "IN_TRANSIT" else "BUSY"
    if status == "UNLOADING":
        for job in jobs(db, voyage):
            if job.cargo_id is None or job.kind == "PICKUP_TRUCK":
                job.status = "COMPLETED"
    audit(db, "line.milestone", voyage.id, actor, status=status, source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def receipt(db, actor, voyage_id, cargo_id, quantity, receiver_name):
    lock_writes(db)
    voyage = require(db, CargoVoyage, voyage_id)
    view_access(db, actor, voyage)
    member = next((m for m in members(db, voyage) if m.cargo_id == cargo_id), None)
    if not member:
        raise HTTPException(404, "Cargo not found on this departure.")
    booking, cargo = db.get(Booking, member.booking_id), db.get(CargoRequest, cargo_id)
    if actor.role_id == "receiver":
        if cargo.organization_id != actor.organization_id:
            raise HTTPException(404, "Consignment not found for this receiver.")
    else:
        coordinate(actor, voyage)
    if not booking or booking.status not in {"UNLOADING", "LAST_MILE"}:
        raise HTTPException(409, "Record unloading before recording the individual door receipt.")
    if quantity > cargo.weight_tonnes + 1e-9:
        raise HTTPException(422, "Received quantity exceeds the accepted consignment.")
    shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
    if shipment.operational_data.get("pod_required") and not shipment.operational_data.get("pod_verified"):
        raise HTTPException(409, "Verify the active receiver delivery challenge before recording the receipt.")
    now = utcnow().isoformat()
    member.receipt = {"quantity_tonnes": quantity, "receiver_name": receiver_name, "recorded_by": actor.id, "recorded_at": now, "source": "SIMULATED application receipt; not a legal digital signature", "receiver_verified": bool(shipment.operational_data.get("pod_verified")), "shortage_tonnes": round(cargo.weight_tonnes - quantity, 3)}
    member.status = booking.status = cargo.status = "DELIVERED"
    shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
    shipment.status, shipment.progress = "DELIVERED", 1
    shipment.operational_data = {**shipment.operational_data, "quantity_received_tonnes": quantity, "delivery_signature": receiver_name, "receipt_source": "SIMULATED"}
    db.add(TrackingEvent(id=uid("event"), shipment_id=shipment.id, status="DELIVERED", description=f"Individual door delivery receipt recorded by {actor.role_id} (simulated).", latitude=shipment.latitude, longitude=shipment.longitude))
    for job in jobs(db, voyage):
        if job.cargo_id == cargo_id and job.status == "ACCEPTED":
            job.status = "COMPLETED"
    if all(m.status in {"DELIVERED", "CANCELLED"} for m in members(db, voyage)):
        voyage.status = "COMPLETED"
    # Vessel state follows common water activity, not a customer's final truck.
    other_active = any(v.id != voyage.id and v.status == "CONFIRMED" and any(db.get(Booking, m.booking_id).status in {"LOADING", "IN_TRANSIT"} for m in members(db, v) if m.booking_id) for v in db.scalars(select(CargoVoyage).where(CargoVoyage.vessel_id == voyage.vessel_id)))
    db.get(Vessel, voyage.vessel_id).state = "BUSY" if other_active else "AVAILABLE"
    audit(db, "line.receipt", member.id, actor, quantity=quantity, source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def disrupt(db, actor, voyage_id):
    lock_writes(db)
    voyage = require(db, CargoVoyage, voyage_id)
    coordinate(actor, voyage)
    if voyage.status != "CONFIRMED" or any(db.get(Booking, m.booking_id).status not in {"CONFIRMED", "SCHEDULED", "CANCELLED"} for m in members(db, voyage)):
        raise HTTPException(409, "This recovery supports a vessel withdrawal before pickup only.")
    db.get(Vessel, voyage.vessel_id).maintenance_status = "MAINTENANCE"
    for member in members(db, voyage):
        if member.status == "CANCELLED":
            continue
        member.status = "DISRUPTED"
        booking, cargo = db.get(Booking, member.booking_id), db.get(CargoRequest, member.cargo_id)
        # Close the old simulated commitment before seeking a new, separately approved one.
        booking.status, cargo.status = "CANCELLED", "POSTED"
        db.scalar(select(InvoiceRecord).where(InvoiceRecord.booking_id == booking.id)).status = "VOID"
        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
        shipment.status = "REPLANNING"
        db.add(TrackingEvent(id=uid("event"), shipment_id=shipment.id, status="REPLANNING", description="Vessel withdrew before pickup; original invoice voided, new terms require owner approval.", latitude=shipment.latitude, longitude=shipment.longitude))
    release(db, voyage, "DISRUPTED")
    audit(db, "line.predeparture_disruption", voyage.id, actor, source="SIMULATED")
    db.commit()
    return serialize(db, actor, voyage)


def recovery_options(db, actor, voyage):
    coordinate(actor, voyage)
    if voyage.status != "DISRUPTED":
        raise HTTPException(409, "Withdraw the unavailable vessel before seeking replacement offers.")
    cargos = [db.get(CargoRequest, m.cargo_id) for m in members(db, voyage) if m.status == "DISRUPTED"]
    options, rejected = [], []
    for vessel in db.scalars(select(Vessel)):
        if vessel.id == voyage.vessel_id:
            continue
        try:
            plan = build_plan(db, cargos, vessel)
            options.append({"vessel_id": vessel.id, "vessel_name": vessel.name, "departure": plan["departure"], "total_cost": sum(m["total_cost"] for m in plan["members"]), "covers_modeled_costs": plan["economics"]["covers_modeled_costs"], "cargo_ids": [c.id for c in cargos]})
        except HTTPException as error:
            rejected.append({"vessel_id": vessel.id, "reason": error.detail})
    return {"options": options, "rejected": rejected, "requires_new_quotes_and_provider_acceptance": True, "source": "SIMULATED pre-pickup alternatives"}


def impact(db, actor):
    rows = []
    for voyage in db.scalars(select(CargoVoyage)):
        if voyage.coordinator_org_id != actor.organization_id:
            continue
        for member in members(db, voyage):
            if not member.booking_id or member.status not in ACTIVE_BOOKING_STATES | {"DELIVERED"}:
                continue
            booking = db.get(Booking, member.booking_id)
            quote = db.get(LineQuote, member.quote_id)
            rows.append((voyage, member, booking, quote))
    selected = sum(db.get(CargoRequest, m.cargo_id).weight_tonnes for v, m, b, q in rows)
    completed = sum((m.receipt or {}).get("quantity_tonnes", 0) for v, m, b, q in rows if m.status == "DELIVERED")
    full_co2 = sum(q.snapshot["road_baseline"]["emissions_kg"] - q.snapshot["emissions_kg"] for v, m, b, q in rows)
    connecting = sum(q.snapshot["first_mile_trips"] + q.snapshot["last_mile_trips"] for v, m, b, q in rows)
    return {"selected_water_tonnes": selected, "completed_water_tonnes": completed, "estimated_full_delivery_co2_avoided_kg": round(full_co2, 2),
        "long_haul_truck_equivalents": sum(q.snapshot["road_baseline"]["truck_trips"] for v, m, b, q in rows), "connecting_truck_trips": connecting,
        "selected_deliveries": len(rows), "completed_deliveries": sum(m.status == "DELIVERED" for v, m, b, q in rows),
        "source": "Record-derived selected tonnes and coordinator receipt quantities. CO₂ is a synthetic tonne-km estimate for the full delivery, not measured/certified savings; no net truck-removal claim."}
