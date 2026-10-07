from datetime import timedelta
from sqlalchemy import select
from backend.models import TerminalCapability, TerminalSlot, Booking
from backend.services.timeutils import dt, overlaps
from feasibility.vessel_constraints.checks import ACTIVE_BOOKING_STATES


def terminal_checks(db, cargo, vessel, terminal):
    capability = db.scalar(
        select(TerminalCapability).where(TerminalCapability.terminal_id == terminal.id)
    )
    if not capability:
        return [f"{terminal.name}: missing verified capability record."]
    reasons = []
    from backend.models import TerminalResource
    from backend.services.terminal_resources import requirements

    resources = list(
        db.scalars(
            select(TerminalResource).where(TerminalResource.terminal_id == terminal.id)
        )
    )
    if resources:
        for kind, quantity in requirements(cargo).items():
            if not any(
                resource.active
                and resource.kind == kind
                and resource.capacity >= quantity
                and (kind != "BERTH" or vessel.length <= resource.max_vessel_length)
                for resource in resources
            ):
                reasons.append(
                    f"{terminal.name}: configured {kind.lower()} resource unavailable."
                )
    if capability.operational_status != "OPEN":
        reasons.append(
            f"{terminal.name}: terminal is {capability.operational_status.lower()}."
        )
    if cargo.cargo_type not in capability.cargo_types:
        reasons.append(f"{terminal.name}: cannot handle {cargo.cargo_type}.")
    if vessel.length > capability.jetty_length:
        reasons.append(f"{terminal.name}: vessel length exceeds jetty limit.")
    if vessel.loaded_draft + 0.2 > capability.approach_channel:
        reasons.append(f"{terminal.name}: approach channel draft limit exceeded.")
    if cargo.weight_tonnes > capability.available_storage:
        reasons.append(f"{terminal.name}: insufficient staging/storage capacity.")
    if not capability.road_access and (
        cargo.first_mile_required or cargo.last_mile_required
    ):
        reasons.append(f"{terminal.name}: road access required for connecting truck.")
    if (
        cargo.cargo_type in {"steel", "construction"}
        or getattr(cargo, "needs_crane", False)
    ) and (
        not capability.crane_available
        or capability.crane_capacity < min(cargo.weight_tonnes, 10)
    ):
        reasons.append(
            f"{terminal.name}: crane capability does not meet demo 10-tonne lift requirement."
        )
    if (
        cargo.packaging in {"bagged", "pallets", "bales"}
        or getattr(cargo, "needs_forklift", False)
    ) and not capability.forklift_available:
        reasons.append(f"{terminal.name}: forklift required for packaged cargo.")
    if (
        cargo.perishable
        or cargo.cargo_type == "cement"
        or getattr(cargo, "needs_covered_storage", False)
    ) and not capability.covered_storage:
        reasons.append(f"{terminal.name}: covered cargo storage required.")
    return reasons


def next_slot(
    db,
    terminal_id,
    earliest,
    duration_hours=0.75,
    exclude_booking_ids=(),
    cargo=None,
    vessel=None,
):
    if cargo is not None and vessel is not None:
        from backend.services.terminal_resources import next_resource_slot
        from backend.models import TerminalResource

        if db.scalar(
            select(TerminalResource).where(TerminalResource.terminal_id == terminal_id)
        ):
            return next_resource_slot(
                db,
                terminal_id,
                cargo,
                vessel,
                earliest,
                duration_hours,
                exclude_booking_ids,
            )
    candidate = earliest
    slots = []
    for slot in db.scalars(
        select(TerminalSlot).where(TerminalSlot.terminal_id == terminal_id)
    ):
        booking = db.get(Booking, slot.booking_id)
        if (
            booking
            and booking.status in ACTIVE_BOOKING_STATES
            and booking.id not in exclude_booking_ids
        ):
            slots.append(slot)
    for slot in sorted(slots, key=lambda item: dt(item.starts_at)):
        if overlaps(
            candidate,
            candidate + timedelta(hours=duration_hours),
            slot.starts_at,
            slot.ends_at,
        ):
            candidate = dt(slot.ends_at)
    return candidate
