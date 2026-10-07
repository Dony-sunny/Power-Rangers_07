import base64
import hashlib
import hmac
import json
import time
from fastapi import Depends, Header, HTTPException
from backend.config import settings
from backend.database import get_db
from backend.models import User, UserStatus
from sqlalchemy import select

ROLE_LABELS = {
    "shipper": "Shipper procurement",
    "dispatch": "Shipper dispatch",
    "warehouse": "Warehouse",
    "receiver": "Consignee",
    "operator": "Vessel operator",
    "fleet": "Fleet dispatcher",
    "captain": "Captain",
    "terminal": "Terminal operator",
    "control": "3PL control tower",
    "finance": "Finance",
    "compliance": "Compliance & safety",
    "maintenance": "Maintenance",
    "network": "Waterway control",
    "government": "Government analytics",
    "admin": "Platform admin",
}
PERMISSIONS = {
    "cargo_write": {"shipper", "control", "admin"},
    "plan": {"shipper", "dispatch", "control", "admin"},
    "vessel_write": {"operator", "fleet", "admin"},
    "availability_write": {"operator", "fleet", "admin"},
    "book": {"shipper", "control", "admin"},
    "execute": {"dispatch", "fleet", "captain", "terminal", "control", "admin"},
    "recover": {"dispatch", "control", "admin"},
    "metrics": {"government", "network", "control", "admin"},
    "finance": {"finance", "admin"},
    "maintain": {"maintenance", "fleet", "admin"},
    "report": {"captain", "operator", "fleet", "network", "admin"},
    "audit": {"admin", "compliance"},
    "demo_admin": {"admin"},
}
GLOBAL_ROLES = {"admin", "control", "government", "network", "compliance"}
COMMERCIAL_ROLES = {"shipper", "operator", "control", "finance", "admin"}


def get_actor(
    db=Depends(get_db),
    x_demo_role: str = Header(default="shipper"),
    x_demo_user: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    if settings.demo_mode:
        if x_demo_role not in ROLE_LABELS:
            raise HTTPException(403, "Unknown demo role.")
        user_id = x_demo_user or f"demo-{x_demo_role}"
        user = db.get(User, user_id)
        if not user or user.role_id != x_demo_role:
            raise HTTPException(403, "Demo user does not have this role.")
        status = db.scalar(select(UserStatus).where(UserStatus.user_id == user.id))
        if status and status.disabled:
            raise HTTPException(403, "User is disabled.")
        return user
    if not settings.auth_secret or len(settings.auth_secret) < 32:
        raise HTTPException(
            503,
            "Configure a strong AUTH_SECRET and signed bearer identities outside demo mode.",
        )
    try:
        token = (authorization or "").removeprefix("Bearer ")
        payload, signature = token.split(".")
        expected = hmac.new(
            settings.auth_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        claims = json.loads(
            base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        )
        if float(claims["exp"]) <= time.time():
            raise ValueError()
        user = db.get(User, claims["sub"])
        if not user or db.scalar(
            select(UserStatus).where(
                UserStatus.user_id == user.id, UserStatus.disabled == True
            )
        ):
            raise ValueError()
        return user
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "Valid signed bearer identity required.") from None


def permission(actor, name):
    if actor.role_id not in PERMISSIONS[name]:
        raise HTTPException(403, f"Your role cannot perform {name}.")


def cargo_access(actor, cargo):
    if (
        actor.role_id not in GLOBAL_ROLES
        and cargo.organization_id != actor.organization_id
    ):
        raise HTTPException(404, "Record not found.")


def vessel_access(actor, vessel):
    if actor.role_id != "admin" and vessel.organization_id != actor.organization_id:
        raise HTTPException(404, "Record not found.")
