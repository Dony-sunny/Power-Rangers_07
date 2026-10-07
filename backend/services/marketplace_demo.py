"""Additive, repeatable synthetic marketplace examples. Existing work is preserved."""
from datetime import timedelta
from sqlalchemy import select
from backend.models import (CargoRequest, CargoLoadProfile, CargoVoyage, Vessel,
                            VesselAvailability, VesselCertificate, User)
from backend.repositories.common import audit
from backend.services import cargo_lines as lines
from backend.services.timeutils import dt, utcnow


def populate(db):
    base = dt(utcnow()).replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=2)
    day = base.date().isoformat()
    owner, operator, coordinator = (db.get(User, key) for key in ["demo-shipper", "demo-operator", "demo-control"])
    template = db.get(Vessel, "vembanad")
    if not all([owner, operator, coordinator, template]):
        from fastapi import HTTPException
        raise HTTPException(409, "The sample network must be initialized before adding marketplace examples.")
    rows = []
    for offset, (scenario, name) in enumerate([
        ("team", "Demo Kuttanad Cargo"), ("transit", "Demo Vembanad Express"), ("delivered", "Demo Pamba Freight")
    ]):
        key = f"demo-market-{day}-{scenario}"
        start = base + timedelta(days=offset)
        if not db.get(Vessel, key):
            db.add(Vessel(id=key, name=name, organization_id=operator.organization_id,
                vessel_type="BARGE", max_capacity_tonnes=150, max_volume_m3=220,
                length=template.length, beam=template.beam, loaded_draft=template.loaded_draft,
                air_draft=template.air_draft, current_location="Maradu", cargo_categories=template.cargo_categories,
                rate_per_tonne_km=3, compliance_status="PASS",
                trust_metrics={"source": "SYNTHETIC marketplace demonstration"}))
            db.flush()
            db.add(VesselAvailability(id=f"{key}-availability", vessel_id=key, origin="Maradu", destination="Alappuzha",
                available_from=start.isoformat(), available_until=(start + timedelta(days=2)).isoformat(), capacity_tonnes=150, volume_m3=220))
            for kind in ["REGISTRATION", "INSURANCE"]:
                db.add(VesselCertificate(id=f"{key}-{kind.lower()}", vessel_id=key, kind=kind,
                    expires_at=(start + timedelta(days=180)).isoformat(), verified=True))
        cargo_ids = []
        for kind, weight, volume, packaging, piece, count, origin in [
            ("cement", 80, 60, "bagged", .05, 1600, "Kalamassery"),
            ("steel", 58, 40, "bundled", 2, 29, "Maradu"),
        ]:
            cargo_id = f"{key}-{kind}"
            cargo_ids.append(cargo_id)
            if not db.get(CargoRequest, cargo_id):
                db.add(CargoRequest(id=cargo_id, organization_id=owner.organization_id, cargo_type=kind,
                    weight_tonnes=weight, volume_m3=volume, packaging=packaging, origin=origin, destination="Alappuzha",
                    ready_time=start.isoformat(), delivery_deadline=(start + timedelta(days=1, hours=14)).isoformat(),
                    first_mile_required=origin != "Maradu", last_mile_required=False))
                db.flush()
                db.add(CargoLoadProfile(id=f"{cargo_id}-profile", cargo_id=cargo_id, heaviest_piece_tonnes=piece, pieces=count))
        db.commit()
        voyage = db.scalar(select(CargoVoyage).where(CargoVoyage.vessel_id == key).order_by(CargoVoyage.created_at.desc()))
        if not voyage:
            result = lines.propose(db, owner, cargo_ids, key, availability_id=f"{key}-availability")
            for member in result["members"]:
                lines.approve_quote(db, owner, member["quote"]["id"])
            lines.operator_response(db, operator, result["id"], result["version"], True)
            if scenario != "team":
                for job in result["jobs"]:
                    lines.job_response(db, coordinator, job["id"], "ACCEPTED")
                lines.confirm(db, coordinator, result["id"])
                for state in ["SCHEDULED", "LOADING", "IN_TRANSIT"]:
                    lines.milestones(db, coordinator, result["id"], state)
                if scenario == "delivered":
                    lines.milestones(db, coordinator, result["id"], "UNLOADING")
                    for member in result["members"]:
                        lines.receipt(db, coordinator, result["id"], member["cargo_id"], member["weight_tonnes"], "Demo Alappuzha receiver")
            voyage = db.get(CargoVoyage, result["id"])
        rows.append({"id": voyage.id, "status": voyage.status, "scenario": scenario, "boat": name})
    for kind, weight, volume, packaging, piece, count in [("coir", 35, 45, "bales", .1, 350), ("cement", 40, 30, "bagged", .05, 800)]:
        cargo_id = f"demo-market-{day}-browse-{kind}"
        if not db.get(CargoRequest, cargo_id):
            db.add(CargoRequest(id=cargo_id, organization_id=owner.organization_id, cargo_type=kind,
                weight_tonnes=weight, volume_m3=volume, packaging=packaging, origin="Kalamassery", destination="Alappuzha",
                ready_time=base.isoformat(), delivery_deadline=(base + timedelta(days=1, hours=14)).isoformat(),
                first_mile_required=True, last_mile_required=False))
            db.flush()
            db.add(CargoLoadProfile(id=f"{cargo_id}-profile", cargo_id=cargo_id, heaviest_piece_tonnes=piece, pieces=count))
    audit(db, "demo.marketplace_populated", day, None, source="SYNTHETIC", deliveries=len(rows))
    db.commit()
    return {"status": "populated", "source": "SYNTHETIC", "deliveries": rows,
            "notice": "Sample cargo, boats and delivery states added. Existing records were preserved; all transport and provider activity is simulated."}
