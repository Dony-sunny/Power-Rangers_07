from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from backend.database import Base, engine, SessionLocal
from backend.auth import ROLE_LABELS, PERMISSIONS
from backend.models import *

IST = ZoneInfo("Asia/Kolkata")
PLACES = {
    "Kalamassery": (10.052, 76.313),
    "Kochi": (9.970, 76.300),
    "Maradu": (9.944, 76.319),
    "Vaikom": (9.748, 76.396),
    "Thanneermukkom": (9.676, 76.404),
    "Alappuzha": (9.498, 76.338),
}
NODES = [
    ("maradu", "Maradu", 9.944, 76.319),
    ("vaikom", "Vaikom", 9.748, 76.396),
    ("thanneermukkom", "Thanneermukkom", 9.676, 76.404),
    ("alappuzha", "Alappuzha", 9.498, 76.338),
]


def tomorrow():
    return (datetime.now(IST) + timedelta(days=1)).replace(
        hour=8, minute=0, second=0, microsecond=0
    )


def seed(db):
    if db.scalar(select(Organization.id).limit(1)):
        return
    start = tomorrow()
    for key, name, kind in [
        ("shipper-org", "Malabar Build Supply", "SHIPPER"),
        ("competitor-org", "Travancore Materials", "SHIPPER"),
        ("operator-org", "Vembanad Freight Co.", "OPERATOR"),
        ("other-operator", "Pamba Inland Logistics", "OPERATOR"),
        ("terminal-org", "Kerala Terminal Services", "TERMINAL"),
        ("3pl-org", "Jalayatra Control", "LOGISTICS"),
        ("authority-org", "Waterway Network Office", "AUTHORITY"),
        ("government-org", "Kerala Policy Lab", "GOVERNMENT"),
    ]:
        db.add(Organization(id=key, name=name, kind=kind, verified=True))
    for role, label in ROLE_LABELS.items():
        db.add(
            Role(
                id=role,
                label=label,
                permissions=[p for p, roles in PERMISSIONS.items() if role in roles],
            )
        )
    db.flush()
    for role, label in ROLE_LABELS.items():
        org = (
            "shipper-org"
            if role in {"shipper", "dispatch", "warehouse", "receiver", "finance"}
            else "operator-org"
            if role in {"operator", "fleet", "captain", "maintenance"}
            else "terminal-org"
            if role == "terminal"
            else "government-org"
            if role == "government"
            else "authority-org"
            if role in {"network", "compliance"}
            else "3pl-org"
        )
        db.add(User(id=f"demo-{role}", name=label, organization_id=org, role_id=role))
    db.add(
        User(
            id="competitor-user",
            name="Competitor shipper",
            organization_id="competitor-org",
            role_id="shipper",
        )
    )
    for key, name, lat, lon in NODES:
        db.add(WaterwayNode(id=key, name=name, latitude=lat, longitude=lon))
    db.flush()
    for i, (src, dst, distance, depth, clearance) in enumerate(
        [
            ("maradu", "vaikom", 28, 2.4, 6.0),
            ("vaikom", "thanneermukkom", 12, 2.0, 4.7),
            ("thanneermukkom", "alappuzha", 24, 2.2, 5.5),
        ]
    ):
        db.add(
            WaterwaySegment(
                id=f"segment-{i + 1}",
                source_node=src,
                destination_node=dst,
                distance_km=distance,
                available_depth=depth,
                minimum_width=24,
                minimum_bridge_clearance=clearance,
                lock_required=i == 1,
                lock_name="Thanneermukkom demo lock" if i == 1 else None,
                lock_open_hour=6,
                lock_close_hour=20,
                source_date="2026-10-06",
                last_verified=None,
            )
        )
    for i, (key, name, _, _) in enumerate(NODES):
        db.add(
            Terminal(
                id=f"terminal-{key}",
                node_id=key,
                organization_id="terminal-org",
                name=f"{name} cargo terminal",
                handling_rate=55 + i * 3,
                wait_hours=0.25,
                source_name="IWAI terminal name; capabilities are synthetic",
                source_date="2026-10-06",
            )
        )
    db.flush()
    for key, _, _, _ in NODES:
        db.add(
            TerminalCapability(
                id=f"capability-{key}",
                terminal_id=f"terminal-{key}",
                cargo_types=[
                    "cement",
                    "steel",
                    "construction",
                    "coir",
                    "rice",
                    "general",
                ],
                jetty_length=70,
                available_storage=500,
                covered_storage=True,
                crane_available=True,
                crane_capacity=15,
                forklift_available=True,
                forklift_capacity=5,
                road_access=True,
                approach_channel=2.5,
            )
        )
    vessels = [
        ("vembanad", "MV Vembanad", "operator-org", 150, 220, 1.5, 4.0, 0.96, 3.0),
        ("deep-blue", "MV Deep Blue", "other-operator", 160, 240, 2.3, 4.2, 0.99, 2.4),
        ("pamba", "MV Pamba", "other-operator", 150, 210, 1.4, 4.0, 0.93, 3.4),
        ("periyar", "MV Periyar", "operator-org", 100, 160, 1.3, 3.8, 0.86, 3.5),
    ]
    for key, name, org, capacity, volume, draft, air, reliability, rate in vessels:
        db.add(
            Vessel(
                id=key,
                name=name,
                organization_id=org,
                max_capacity_tonnes=capacity,
                max_volume_m3=volume,
                length=38,
                beam=7.5,
                loaded_draft=draft,
                air_draft=air,
                current_location="Maradu",
                cargo_categories=[
                    "cement",
                    "steel",
                    "construction",
                    "coir",
                    "rice",
                    "general",
                ],
                reliability_score=reliability,
                rate_per_tonne_km=rate,
                trust_metrics={
                    "source": "Synthetic demo voyage history",
                    "completed_voyages": 42,
                    "on_time_pct": round(reliability * 100),
                    "cancellation_pct": 2,
                    "claims_pct": 0.5,
                },
            )
        )
    db.flush()
    for key, _, _, capacity, volume, *_ in vessels:
        db.add(
            VesselAvailability(
                id=f"availability-{key}",
                vessel_id=key,
                origin="Maradu",
                destination="Alappuzha",
                available_from=start.isoformat(),
                available_until=(start + timedelta(days=3)).isoformat(),
                capacity_tonnes=capacity,
                volume_m3=volume,
            )
        )
        for kind in ["REGISTRATION", "INSURANCE"]:
            db.add(
                VesselCertificate(
                    id=f"{key}-{kind.lower()}",
                    vessel_id=key,
                    kind=kind,
                    expires_at=(start + timedelta(days=180)).isoformat(),
                    verified=True,
                )
            )
        db.add(
            VesselMaintenanceStatus(
                id=f"maintenance-{key}",
                vessel_id=key,
                status="OPERATIONAL",
                defect="",
                inspection_date=start.date().isoformat(),
                due_date=(start + timedelta(days=30)).date().isoformat(),
                return_to_service=None,
            )
        )
    cargo = [
        (
            "hero-cargo",
            "shipper-org",
            "cement",
            80,
            60,
            "bagged",
            "Kalamassery",
            "Alappuzha",
            start,
            start + timedelta(hours=14),
        ),
        (
            "pool-cargo",
            "shipper-org",
            "steel",
            58,
            48,
            "bundled",
            "Maradu",
            "Alappuzha",
            start,
            start + timedelta(hours=14),
        ),
        (
            "return-cargo",
            "shipper-org",
            "coir",
            62,
            85,
            "bales",
            "Alappuzha",
            "Maradu",
            start + timedelta(hours=12),
            start + timedelta(hours=38),
        ),
        (
            "unserved-cargo",
            "competitor-org",
            "general",
            240,
            320,
            "pallets",
            "Vaikom",
            "Alappuzha",
            start,
            start + timedelta(hours=12),
        ),
    ]
    for (
        key,
        org,
        category,
        weight,
        volume,
        packaging,
        origin,
        destination,
        ready,
        deadline,
    ) in cargo:
        db.add(
            CargoRequest(
                id=key,
                organization_id=org,
                cargo_type=category,
                weight_tonnes=weight,
                volume_m3=volume,
                packaging=packaging,
                origin=origin,
                destination=destination,
                origin_coordinates=list(PLACES[origin]),
                destination_coordinates=list(PLACES[destination]),
                ready_time=ready.isoformat(),
                delivery_deadline=deadline.isoformat(),
                first_mile_required=origin == "Kalamassery",
                last_mile_required=False,
                budget=None,
            )
        )
    db.add(
        CargoPreference(
            id="preference-demo",
            organization_id="shipper-org",
            preferred_operators=["operator-org"],
            ranking_profile="BALANCED",
            recurring_contract={"status": "architecture", "frequency": "Mon/Wed/Fri"},
        )
    )
    db.add(
        VesselAvailability(
            id="availability-vembanad-return",
            vessel_id="vembanad",
            origin="Alappuzha",
            destination="Maradu",
            available_from=(start + timedelta(hours=12)).isoformat(),
            available_until=(start + timedelta(days=3)).isoformat(),
            capacity_tonnes=150,
            volume_m3=220,
        )
    )
    db.add(
        ScheduledService(
            id="nw3-service",
            name="NW-3 Southbound · morning freight",
            vessel_id="periyar",
            departure=(start + timedelta(hours=1)).isoformat(),
            capacity_tonnes=100,
            recurrence="Mon / Wed / Fri · demo instance",
        )
    )
    db.flush()
    for i, (key, _, _, _) in enumerate(NODES):
        arrival = start + timedelta(hours=[1, 4.5, 6.5, 10][i])
        db.add(
            ScheduledServiceStop(
                id=f"service-stop-{i}",
                service_id="nw3-service",
                terminal_id=f"terminal-{key}",
                sequence=i,
                arrival=arrival.isoformat(),
                departure=(arrival + timedelta(minutes=15)).isoformat(),
            )
        )
    from backend.services.terminal_resources import seed_resources

    seed_resources(db)
    from backend.services.analytics import seed_rate_history

    seed_rate_history(db)
    db.commit()


def initialize(reset=False):
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
        from backend.services.terminal_resources import seed_resources

        seed_resources(db)
        from backend.services.analytics import seed_rate_history

        seed_rate_history(db)
        db.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize transparent Jalayatra demo fixtures."
    )
    parser.add_argument("--reset", action="store_true")
    initialize(parser.parse_args().reset)
    print("Demo database ready. All operational values are synthetic.")
