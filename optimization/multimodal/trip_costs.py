"""Disclosed synthetic tariffs, integer paise, whole trips and shared charges."""
import math
from decimal import Decimal, ROUND_HALF_UP

TERMS = {
    "version": "demo-trip-v1",
    "source": "SIMULATED: engineering assumptions, not provider offers",
    "payload_tonnes": 20,
    "truck_volume_m3": 60,
    "pieces_per_trip": 2000,
    "truck_minimum": 2500,
    "road_per_truck_km": 136,
    "connecting_per_truck_km": 160,
    "truck_wait_allowance_hours": 2,
    "truck_wait_per_hour": 400,
    "road_handling_setup": 1000,
    "sailing_sale_fixed": 12000,
    "sailing_operating_fixed": 18000,
    "sailing_operating_per_km": 60,
    "sailing_operating_per_tonne_km": 0.5,
    "terminal_setup": 1500,
    "handling_setup_hours": 0.25,
    "handling_tonnes_per_hour": 100,
}


def minor(value):
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def rupees(value):
    return value / 100


def product(*values):
    result = Decimal("1")
    for value in values:
        result *= Decimal(str(value))
    return minor(result)


def trips(cargo, payload=20, volume=60, pieces_per_trip=2000):
    heaviest = getattr(cargo, "heaviest_piece_tonnes", None)
    # Conservative homogeneous-unit bound; never pack two 12 t units in a 20 t truck.
    unit_limit = min(pieces_per_trip, max(1, math.floor(payload / heaviest + 1e-10))) if heaviest else pieces_per_trip
    return max(1, math.ceil(cargo.weight_tonnes / payload - 1e-10),
               math.ceil((cargo.volume_m3 or 0) / volume - 1e-10),
               math.ceil(getattr(cargo, "pieces", 1) / unit_limit))


def truck_charge(cargo, distance, connecting=False, required=True):
    if not required:
        return 0
    count = trips(cargo)
    # Minimum OR distance tariff per trip; the minimum is never added twice.
    rate = TERMS["connecting_per_truck_km" if connecting else "road_per_truck_km"]
    return count * max(minor(TERMS["truck_minimum"]), product(distance, rate))


def allocate(total_minor, weights):
    """Largest remainder allocation: totals reconcile even for one-paise charges."""
    amounts = [Decimal(str(weight)) for weight in weights]
    total = sum(amounts)
    shares = [Decimal(total_minor) * weight / total for weight in amounts]
    floors = [int(value) for value in shares]
    order = sorted(range(len(shares)), key=lambda i: (-(shares[i] - floors[i]), i))
    for index in order[:total_minor - sum(floors)]:
        floors[index] += 1
    return floors


def handling_hours(weight, terms=None):
    terms = terms or TERMS
    return terms["handling_setup_hours"] + weight / terms["handling_tonnes_per_hour"]


def sailing_economics(weight, distance, variable_rate, sale_minor=None, terms=None):
    terms = terms or TERMS
    selling = minor(terms["sailing_sale_fixed"]) + product(weight, distance, variable_rate)
    operating = minor(terms["sailing_operating_fixed"]) + product(distance, terms["sailing_operating_per_km"]) + product(weight, distance, terms["sailing_operating_per_tonne_km"])
    revenue = selling if sale_minor is None else sale_minor
    return {
        "revenue_minor": revenue,
        "operating_cost_minor": operating,
        "contribution_minor": revenue - operating,
        "covers_modeled_costs": revenue >= operating,
        "source": terms["source"],
        "basis": "Water charges only; truck/terminal charges are disclosed pass-through payables. Excludes tax, finance, platform overhead and unbooked return revenue. Not audited net profit.",
    }
