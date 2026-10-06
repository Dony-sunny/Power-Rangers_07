import logging
import json
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import inspect
from backend.models import AuditEvent

logger = logging.getLogger("jalayatra")


def uid(prefix):
    return f"{prefix}-{uuid4().hex[:12]}"


def record(obj):
    return {
        column.key: getattr(obj, column.key)
        for column in inspect(obj).mapper.column_attrs
    }


def require(db, model, key):
    value = db.get(model, key)
    if value is None:
        raise HTTPException(404, "Record not found.")
    return value


def audit(db, event, entity_id, actor=None, **details):
    db.add(
        AuditEvent(
            id=uid("audit"),
            actor_id=getattr(actor, "id", None),
            organization_id=getattr(actor, "organization_id", None),
            event=event,
            entity_id=entity_id,
            details=details,
        )
    )
    logger.info(
        json.dumps(
            {"event": event, "entity_id": entity_id, "details": details},
            ensure_ascii=False,
        )
    )
