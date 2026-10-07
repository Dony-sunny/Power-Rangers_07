from datetime import timedelta
from sqlalchemy import select
from fastapi import HTTPException
from backend.models import *
from backend.repositories.common import uid, record
from backend.services.timeutils import dt, overlaps
from feasibility.vessel_constraints.checks import ACTIVE_BOOKING_STATES


def seed_resources(db):
    for terminal in db.scalars(select(Terminal)):
        if db.scalar(
            select(TerminalResource).where(TerminalResource.terminal_id == terminal.id)
        ):
            continue
        capability = db.scalar(
            select(TerminalCapability).where(
                TerminalCapability.terminal_id == terminal.id
            )
        )
        for kind, capacity, active in [
            ("BERTH", 1, True),
            ("CRANE", 1, capability.crane_available),
            ("FORKLIFT", 1, capability.forklift_available),
            ("STORAGE", capability.available_storage, True),
            ("TRUCK_GATE", 1, capability.road_access),
        ]:
            db.add(
                TerminalResource(
                    id=uid("resource"),
                    terminal_id=terminal.id,
                    name=f"{terminal.name} · {kind.lower()}",
                    kind=kind,
                    capacity=capacity,
                    active=active,
                    max_vessel_length=capability.jetty_length,
                )
            )
    db.flush()


def apply_group_requirements(merged, cargos):
    """Preserve every member's handling needs without changing its cargo category."""
    merged.needs_crane = any(
        item.cargo_type in {"steel", "construction"} for item in cargos
    )
    merged.needs_forklift = any(
        item.packaging in {"bagged", "pallets", "bales"} for item in cargos
    )
    merged.needs_covered_storage = any(
        item.perishable or item.cargo_type == "cement" for item in cargos
    )
    return merged


def requirements(cargo):
    required = {"BERTH": 1, "STORAGE": cargo.weight_tonnes}
    if cargo.cargo_type in {"steel", "construction"} or getattr(
        cargo, "needs_crane", False
    ):
        required["CRANE"] = 1
    if cargo.packaging in {"bagged", "pallets", "bales"} or getattr(
        cargo, "needs_forklift", False
    ):
        required["FORKLIFT"] = 1
    return required


def reservations(db, resource, exclusions):
    result = []
    for reservation in db.scalars(
        select(ResourceReservation).where(
            ResourceReservation.resource_id == resource.id
        )
    ):
        if reservation.booking_id in exclusions:
            continue
        booking = (
            db.get(Booking, reservation.booking_id) if reservation.booking_id else None
        )
        if booking and booking.status not in ACTIVE_BOOKING_STATES:
            if not booking.pool_id or not any(
                member.status in ACTIVE_BOOKING_STATES
                for member in db.scalars(
                    select(Booking).where(Booking.pool_id == booking.pool_id)
                )
            ):
                continue
        result.append(reservation)
    # A Cargo Lines departure owns reservations independently of any first member.
    from backend.services.timeutils import utcnow
    for job in db.scalars(select(ProviderJob).where(ProviderJob.terminal_resource_id == resource.id,
                                                  ProviderJob.status.in_(["PENDING", "ACCEPTED"]))):
        voyage = db.get(CargoVoyage, job.voyage_id)
        if f"voyage:{voyage.id}" in exclusions or voyage.status in {"CANCELLED", "EXPIRED", "DECLINED", "DISRUPTED", "COMPLETED"}:
            continue
        if voyage.status == "HELD" and dt(voyage.expires_at) <= utcnow():
            continue
        result.append(job)
    return result


def peak_quantity(items, start, end):
    points = {dt(start), dt(end)}
    for item in items:
        if overlaps(start, end, item.starts_at, item.ends_at):
            points.add(max(dt(start), dt(item.starts_at)))
            points.add(min(dt(end), dt(item.ends_at)))
    return max(
        (
            sum(
                item.quantity
                for item in items
                if dt(item.starts_at) <= point < dt(item.ends_at)
            )
            for point in points
            if point < dt(end)
        ),
        default=0,
    )


def choose_resources(
    db, terminal_id, cargo, vessel, start, end, exclusions=(), storage_exclusions=None
):
    resources = list(
        db.scalars(
            select(TerminalResource)
            .where(TerminalResource.terminal_id == terminal_id)
            .order_by(TerminalResource.id)
        )
    )
    chosen, conflicts = [], []
    for kind, quantity in requirements(cargo).items():
        eligible = [
            resource
            for resource in resources
            if resource.active
            and resource.kind == kind
            and resource.capacity >= quantity
            and (kind != "BERTH" or vessel.length <= resource.max_vessel_length)
        ]
        selected = next(
            (
                resource
                for resource in eligible
                if peak_quantity(
                    reservations(
                        db,
                        resource,
                        storage_exclusions
                        if kind == "STORAGE" and storage_exclusions is not None
                        else exclusions,
                    ),
                    start,
                    end,
                )
                + quantity
                <= resource.capacity
            ),
            None,
        )
        if not selected:
            conflicts.append(f"{kind}: unavailable or overlapping resource reservation")
        else:
            chosen.append((selected, quantity))
    return chosen, conflicts


def next_resource_slot(
    db, terminal_id, cargo, vessel, earliest, duration_hours=0.75, exclusions=()
):
    candidate = earliest
    resources = list(
        db.scalars(
            select(TerminalResource).where(TerminalResource.terminal_id == terminal_id)
        )
    )
    for _ in range(100):
        _, conflicts = choose_resources(
            db,
            terminal_id,
            cargo,
            vessel,
            candidate,
            candidate + timedelta(hours=duration_hours),
            exclusions,
        )
        if not conflicts:
            return candidate
        ends = [
            dt(item.ends_at)
            for resource in resources
            for item in reservations(db, resource, exclusions)
            if overlaps(
                candidate,
                candidate + timedelta(hours=duration_hours),
                item.starts_at,
                item.ends_at,
            )
        ]
        if not ends:
            return candidate  # Hard capability checks reject unavailable resources.
        candidate = min(end for end in ends if end > candidate)
    raise HTTPException(
        409,
        "Terminal queue exceeds bounded slot search; choose another terminal or date.",
    )


def reserve_plan(db, booking, cargo, vessel, service_id=None):
    exclusions = [booking.id]
    if service_id:
        exclusions += [
            item.booking_id
            for item in db.scalars(
                select(ScheduledCapacityBooking).where(
                    ScheduledCapacityBooking.service_id == service_id
                )
            )
        ]
    for terminal_id, key in [
        (booking.origin_terminal_id, "loading_start"),
        (booking.destination_terminal_id, "unloading_start"),
    ]:
        start = dt(booking.plan_snapshot[key])
        end = start + timedelta(hours=0.75)
        chosen, conflicts = choose_resources(
            db, terminal_id, cargo, vessel, start, end, exclusions, [booking.id]
        )
        if conflicts:
            raise HTTPException(
                409,
                {
                    "message": "Terminal resources changed before booking.",
                    "reasons": conflicts,
                },
            )
        for resource, quantity in chosen:
            # A common scheduled voyage shares berth/equipment once; storage sums per cargo.
            if (
                service_id
                and resource.kind != "STORAGE"
                and any(
                    item.booking_id in exclusions
                    and item.booking_id != booking.id
                    and overlaps(start, end, item.starts_at, item.ends_at)
                    for item in db.scalars(
                        select(ResourceReservation).where(
                            ResourceReservation.resource_id == resource.id
                        )
                    )
                )
            ):
                continue
            db.add(
                ResourceReservation(
                    id=uid("resource-booking"),
                    resource_id=resource.id,
                    booking_id=booking.id,
                    starts_at=start.isoformat(),
                    ends_at=end.isoformat(),
                    quantity=quantity,
                    description=f"{cargo.cargo_type} {cargo.weight_tonnes:g} t",
                )
            )
    db.flush()


def calendar(db, terminal_ids):
    resources = [
        resource
        for resource in db.scalars(select(TerminalResource))
        if resource.terminal_id in terminal_ids
    ]
    rows = [item for resource in resources for item in reservations(db, resource, ())]
    return {
        "resources": [record(resource) for resource in resources],
        "reservations": [record(item) for item in rows],
        "queue": sorted(
            [
                record(item)
                for item in rows
                if db.get(TerminalResource, item.resource_id).kind == "BERTH"
            ],
            key=lambda item: item["starts_at"],
        ),
        "source": "Configured demo berth/equipment/storage resources; simultaneous reservations are capacity checked",
    }
