from sqlalchemy import select
from backend.models import Booking, CargoRequest
from backend.services.timeutils import overlaps

ACTIVE_BOOKING_STATES = {
    "CONFIRMED",
    "SCHEDULED",
    "LOADING",
    "IN_TRANSIT",
    "UNLOADING",
    "LAST_MILE",
    "REPLANNING",
}


def reserved(db, vessel_id, start, end, exclude_booking_ids=()):
    weight = volume = 0.0
    cargos = []
    for booking in db.scalars(select(Booking).where(Booking.vessel_id == vessel_id)):
        if (
            booking.id in exclude_booking_ids
            or booking.status not in ACTIVE_BOOKING_STATES
            or not overlaps(start, end, booking.departure, booking.eta)
        ):
            continue
        cargo = db.get(CargoRequest, booking.cargo_id)
        weight += cargo.weight_tonnes
        volume += cargo.volume_m3 or 0
        cargos.append(cargo)
    return weight, volume, cargos


def vessel_checks(cargo, vessel, availability, occupied_weight=0, occupied_volume=0):
    reasons = []
    capacity = (
        min(vessel.max_capacity_tonnes, availability.capacity_tonnes) - occupied_weight
    )
    volume = min(vessel.max_volume_m3, availability.volume_m3) - occupied_volume
    if cargo.weight_tonnes > capacity + 1e-9:
        reasons.append(
            f"Weight {cargo.weight_tonnes:g} t exceeds available capacity {max(0, capacity):g} t."
        )
    if cargo.volume_m3 is not None and cargo.volume_m3 > volume + 1e-9:
        reasons.append(
            f"Volume {cargo.volume_m3:g} m³ exceeds available volume {max(0, volume):g} m³."
        )
    if cargo.cargo_type not in vessel.cargo_categories:
        reasons.append(
            f"Cargo category {cargo.cargo_type} is incompatible with this vessel."
        )
    if cargo.temperature_control_required and not vessel.cold_chain:
        reasons.append("Temperature-controlled equipment is required and unavailable.")
    if cargo.hazardous and not vessel.hazardous_certified:
        reasons.append(
            "Dangerous cargo requires verified vessel certification and additional compliance review."
        )
    if vessel.maintenance_status != "OPERATIONAL" or vessel.state == "MAINTENANCE":
        reasons.append("Vessel is blocked by maintenance availability.")
    if not availability.active:
        reasons.append("Vessel availability was withdrawn.")
    return reasons
