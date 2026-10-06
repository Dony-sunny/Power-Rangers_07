import math
from datetime import timedelta
from data.seed.network import PLACES
from backend.models import WaterwayNode
from backend.services.timeutils import dt
from optimization.config import RATES, EMISSIONS


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
        "road_freight": round(
            cargo.weight_tonnes * distance * RATES["road_per_tonne_km"], 2
        ),
        "handling": round(cargo.weight_tonnes * RATES["road_handling_per_tonne"], 2),
    }
    hours = distance / RATES["road_speed_kmh"] + 0.75
    eta = dt(cargo.ready_time) + timedelta(hours=hours)
    sla = eta <= dt(cargo.delivery_deadline)
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
        "first_mile_truck": round(
            weight * first_km * RATES["first_last_per_tonne_km"], 2
        ),
        "origin_handling": round(weight * origin_terminal.handling_rate, 2),
        "storage_waiting": round(weight * waiting * RATES["storage_per_tonne_hour"], 2),
        "water_freight": round(weight * distance * vessel.rate_per_tonne_km, 2),
        "destination_handling": round(weight * destination_terminal.handling_rate, 2),
        "last_mile_truck": round(
            weight * last_km * RATES["first_last_per_tonne_km"], 2
        ),
    }
