from sqlalchemy import select
from backend.models import AuditEvent


def flood_enabled(db):
    state = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.event == "demo.flood")
        .order_by(AuditEvent.timestamp.desc())
        .limit(1)
    )
    return bool(state and state.details.get("enabled"))
