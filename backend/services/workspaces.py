from sqlalchemy import select
from backend.models import *
from backend.auth import GLOBAL_ROLES, COMMERCIAL_ROLES, ROLE_LABELS
from backend.repositories.common import record
from backend.services.bookings import booking_access
from fastapi import HTTPException


def workspace(db, actor):
    role = actor.role_id
    vessel_query = select(Vessel)
    if role not in GLOBAL_ROLES and role not in {"shipper", "dispatch"}:
        vessel_query = vessel_query.where(
            Vessel.organization_id == actor.organization_id
        )
    vessels = list(db.scalars(vessel_query))
    vessel_records = []
    for vessel in vessels:
        row = record(vessel)
        if role not in COMMERCIAL_ROLES:
            for field in ["rate_per_tonne_km", "trust_metrics"]:
                row.pop(field, None)
        vessel_records.append(row)
    cargo_query = select(CargoRequest).order_by(CargoRequest.created_at.desc())
    if role not in GLOBAL_ROLES:
        cargo_query = cargo_query.where(
            CargoRequest.organization_id == actor.organization_id
        )
    cargos = (
        list(db.scalars(cargo_query))
        if role
        in {
            "shipper",
            "dispatch",
            "warehouse",
            "receiver",
            "control",
            "government",
            "network",
            "admin",
            "finance",
            "compliance",
        }
        else []
    )
    cargo_records = []
    for item in cargos:
        row = record(item)
        if role not in COMMERCIAL_ROLES:
            row.pop("budget", None)
        cargo_records.append(row)
    shipments = []
    for shipment in db.scalars(select(Shipment)):
        booking = db.get(Booking, shipment.booking_id)
        try:
            booking_access(db, actor, booking)
        except HTTPException:
            continue
        row = record(booking)
        if role not in COMMERCIAL_ROLES:
            for field in ["total_cost", "cost_breakdown", "risk", "plan_snapshot"]:
                row.pop(field, None)
            row["approved_route"] = booking.plan_snapshot.get("route")
        cargo = record(db.get(CargoRequest, booking.cargo_id))
        cargo.pop("budget", None)
        cargo.pop("organization_id", None)
        shipments.append(
            {
                "shipment": record(shipment),
                "booking": row,
                "cargo": cargo,
                "vessel_name": db.get(Vessel, booking.vessel_id).name
                if booking.vessel_id
                else "Road carrier",
            }
        )
    terminals = list(db.scalars(select(Terminal)))
    terminal_records = [
        {
            **record(t),
            "capability": record(
                db.scalar(
                    select(TerminalCapability).where(
                        TerminalCapability.terminal_id == t.id
                    )
                )
            ),
        }
        for t in terminals
    ]
    visible_booking_ids = {item["booking"]["id"] for item in shipments}
    slots = [
        record(slot)
        for slot in db.scalars(select(TerminalSlot))
        if role in GLOBAL_ROLES
        or role == "terminal"
        and db.get(Terminal, slot.terminal_id).organization_id == actor.organization_id
        or slot.booking_id in visible_booking_ids
    ]
    response = {
        "actor": record(actor),
        "organization": record(db.get(Organization, actor.organization_id)),
        "role_label": ROLE_LABELS[role],
        "cargo": cargo_records,
        "vessels": vessel_records,
        "availability": [
            record(a)
            for a in db.scalars(select(VesselAvailability))
            if a.vessel_id in {v.id for v in vessels}
        ],
        "shipments": shipments,
        "terminals": terminal_records,
        "slots": slots,
        "nodes": [record(n) for n in db.scalars(select(WaterwayNode))],
        "segments": [record(s) for s in db.scalars(select(WaterwaySegment))],
        "services": [record(s) for s in db.scalars(select(ScheduledService))],
        "certificates": [
            record(c)
            for c in db.scalars(select(VesselCertificate))
            if c.vessel_id in {v.id for v in vessels}
        ],
        "maintenance": [
            record(m)
            for m in db.scalars(select(VesselMaintenanceStatus))
            if m.vessel_id in {v.id for v in vessels}
        ],
        "reports": [record(r) for r in db.scalars(select(NavigationReport))]
        if role in {"captain", "operator", "fleet", "network", "admin", "compliance"}
        else [],
    }
    if role in {"finance", "admin", "operator"}:
        invoices = [
            i
            for i in db.scalars(select(InvoiceRecord))
            if i.booking_id in visible_booking_ids
        ]
        response["invoices"] = [record(i) for i in invoices]
        response["payments"] = [
            record(p)
            for p in db.scalars(select(PaymentRecord))
            if p.invoice_id in {i.id for i in invoices}
        ]
    if role in {"admin", "compliance"}:
        response["audit"] = [
            record(a)
            for a in db.scalars(
                select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(100)
            )
        ]
    if role == "admin":
        response["organizations"] = [
            record(o) for o in db.scalars(select(Organization))
        ]
        response["users"] = [
            {
                **record(u),
                "disabled": bool(
                    db.scalar(
                        select(UserStatus).where(
                            UserStatus.user_id == u.id, UserStatus.disabled == True
                        )
                    )
                ),
            }
            for u in db.scalars(select(User))
        ]
    return response
