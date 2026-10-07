from sqlalchemy import select
from backend.models import (CoordinationGrant, CargoLoadProfile, TerminalRateCard,
                            TruckResource, Terminal, TerminalCapability, CargoRequest, User)
from optimization.multimodal.trip_costs import TERMS


def seed_lines(db):
    """Idempotent additive demo setup; never reset customer records."""
    if not db.get(CoordinationGrant, "demo-coordination"):
        db.add(CoordinationGrant(id="demo-coordination", owner_org_id="shipper-org", coordinator_org_id="3pl-org"))
    for role in ["operator", "fleet", "captain", "maintenance"]:
        key = f"demo-pamba-{role}"
        if not db.get(User, key):
            db.add(User(id=key, organization_id="other-operator", role_id=role, name=f"Pamba demo {role}"))
    for terminal in db.scalars(select(Terminal)):
        if db.scalar(select(TerminalRateCard).where(TerminalRateCard.terminal_id == terminal.id)):
            continue
        cap = db.scalar(select(TerminalCapability).where(TerminalCapability.terminal_id == terminal.id))
        db.add(TerminalRateCard(id=f"card-{terminal.id}-v1", terminal_id=terminal.id, version=1, terms={
            "cargo_categories": cap.cargo_types, "packaging": ["bagged", "bundled", "bales", "pallets", "bulk", "crates"],
            "setup_minor": int(TERMS["terminal_setup"] * 100), "per_tonne_minor": round(terminal.handling_rate * 100),
            "storage_per_tonne_hour_minor": 300,
            "handling_setup_hours": TERMS["handling_setup_hours"], "handling_tonnes_per_hour": TERMS["handling_tonnes_per_hour"],
            "equipment_crew_included": True, "operating_hours": ["00:00", "24:00"],
            "adjustment_rule": "NONE: material changes require a new quote", "minimum_rule": "setup plus quantity",
            "waiting_allowance_hours": terminal.wait_hours, "repositioning_minor": 0,
        }))
    for index in range(1, 13):
        key = f"demo-truck-{index:02d}"
        if not db.get(TruckResource, key):
            db.add(TruckResource(id=key, organization_id="3pl-org", name=f"Demo 20 t truck {index:02d}", cargo_categories=["cement", "steel", "construction", "coir", "rice", "general"]))
    for key, piece, count in [("hero-cargo", .05, 1600), ("pool-cargo", 2, 29), ("return-cargo", .2, 310)]:
        if db.get(CargoRequest, key) and not db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == key)):
            db.add(CargoLoadProfile(id=f"profile-{key}", cargo_id=key, heaviest_piece_tonnes=piece, pieces=count))
    db.flush()
