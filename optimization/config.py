PROFILES = {
    "BALANCED": {
        "capacity": 0.20,
        "schedule": 0.20,
        "cost": 0.25,
        "reliability": 0.25,
        "carbon": 0.10,
    },
    "CHEAPEST": {
        "capacity": 0.10,
        "schedule": 0.10,
        "cost": 0.65,
        "reliability": 0.10,
        "carbon": 0.05,
    },
    "FASTEST": {
        "capacity": 0.10,
        "schedule": 0.65,
        "cost": 0.10,
        "reliability": 0.10,
        "carbon": 0.05,
    },
    "GREENEST": {
        "capacity": 0.10,
        "schedule": 0.10,
        "cost": 0.10,
        "reliability": 0.10,
        "carbon": 0.60,
    },
    "MOST_RELIABLE": {
        "capacity": 0.10,
        "schedule": 0.10,
        "cost": 0.10,
        "reliability": 0.65,
        "carbon": 0.05,
    },
}
RATES = {
    "road_per_tonne_km": 6.8,
    "road_handling_per_tonne": 70,
    "first_last_per_tonne_km": 8.0,
    "storage_per_tonne_hour": 3.0,
    "road_speed_kmh": 32,
    "water_speed_kmh": 10,
    "handling_hours": 0.75,
}
EMISSIONS = {
    "road_kg_per_tonne_km": 0.105,
    "water_kg_per_tonne_km": 0.028,
    "source_name": "Prototype assumptions; not certified emission factors",
    "source_date": "2026-10-06",
    "verification_status": "SIMULATED",
}
UNDER_KEEL_MARGIN = 0.2
TRUCK_CAPACITY_TONNES = 20
