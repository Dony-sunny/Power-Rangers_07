import math
from datetime import timedelta
from data.seed.network import PLACES
from backend.models import WaterwayNode
from backend.services.timeutils import dt
from optimization.config import RATES, EMISSIONS
from optimization.multimodal.trip_costs import TERMS, minor, product, rupees, trips, truck_charge


def coordinates(place, supplied=None):
    if supplied:
        return tuple(supplied)
    return next(
        (
            coords
            for name, coords in PLACES.items()
            if name.casefold() == place.casefold()
        ),
        None,
    )


def road_distance(first, second):
    lat1, lon1, lat2, lon2 = map(math.radians, (*first, *second))
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * math.asin(min(1, math.sqrt(a))) * 1.35


def carbon(tonnes, distance_km, mode):
    return round(tonnes * distance_km * EMISSIONS[f"{mode.lower()}_kg_per_tonne_km"], 2)


def road_plan(cargo, flood=False):
    origin = coordinates(cargo.origin, cargo.origin_coordinates)
    destination = coordinates(cargo.destination, cargo.destination_coordinates)
    if not origin or not destination:
        return {
            "mode": "ROAD",
            "feasible": False,
            "reasons": ["Coordinates needed to estimate road distance."],
            "total_cost": None,
        }
    distance = road_distance(origin, destination)
    breakdown = {
        "road_freight": rupees(truck_charge(cargo, distance)),
        "handling": round(cargo.weight_tonnes * RATES["road_handling_per_tonne"], 2),
        "handling_setup": TERMS["road_handling_setup"],
    }
    hours = distance / RATES["road_speed_kmh"] + 0.75
    eta = dt(cargo.ready_time) + timedelta(hours=hours)
    receiving_start = getattr(cargo, "receiving_from", None)
    receiving_end = getattr(cargo, "receiving_until", None)
    wait = max(0, (dt(receiving_start) - eta).total_seconds() / 3600) if receiving_start else 0
    eta += timedelta(hours=wait)
    hours += wait
    breakdown["truck_waiting"] = rupees(product(trips(cargo), max(0, wait - TERMS["truck_wait_allowance_hours"]), TERMS["truck_wait_per_hour"]))
    sla = eta <= dt(cargo.delivery_deadline) and (not receiving_end or eta <= dt(receiving_end))
    return {
        "mode": "ROAD",
        "feasible": sla and not flood,
        "sla": sla and not flood,
        "total_cost": round(sum(breakdown.values()), 2),
        "breakdown": breakdown,
        "emissions_kg": carbon(cargo.weight_tonnes, distance, "road"),
        "eta": eta.isoformat(),
        "departure": cargo.ready_time,
        "hours": round(hours, 2),
        "road_km": round(distance, 2),
        "water_km": 0,
        "handoffs": 1,
        "truck_trips": trips(cargo),
        "tariff_version": TERMS["version"],
        "tariff_source": TERMS["source"],
        "volume_verified": cargo.volume_m3 is not None,
        "reliability": 0.90,
        "reasons": ["Simulated flood: road corridor unavailable."]
        if flood
        else []
        if sla
        else ["Road ETA misses delivery deadline."],
    }


def water_cost(
    cargo,
    vessel,
    origin_terminal,
    destination_terminal,
    first_km,
    last_km,
    distance,
    waiting,
):
    weight = cargo.weight_tonnes
    return {
        "first_mile_truck": rupees(truck_charge(cargo, first_km, True, cargo.first_mile_required)),
        "origin_handling": rupees(product(weight, origin_terminal.handling_rate)),
        "origin_handling_setup": TERMS["terminal_setup"],
        "storage_waiting": round(weight * waiting * RATES["storage_per_tonne_hour"], 2),
        "water_freight": rupees(product(weight, distance, vessel.rate_per_tonne_km)),
        "sailing_fixed": TERMS["sailing_sale_fixed"],
        "destination_handling": rupees(product(weight, destination_terminal.handling_rate)),
        "destination_handling_setup": TERMS["terminal_setup"],
        "last_mile_truck": rupees(truck_charge(cargo, last_km, True, cargo.last_mile_required)),
    }
