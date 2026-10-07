from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import Field
from backend.models import Organization, User, Role, UserStatus
from backend.auth import get_actor, permission, ROLE_LABELS
from backend.database import get_db
from backend.repositories.common import uid, require, record, audit
from backend.schemas.requests import StrictModel

router = APIRouter(prefix="/api/admin", tags=["administration"])


class OrganizationCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    kind: str = Field(
        pattern="^(shipper|operator|logistics|terminal|authority|government)$"
    )
    verified: bool = False


class UserCreate(StrictModel):
    name: str = Field(min_length=2, max_length=100)
    organization_id: str
    role_id: str


class UserUpdate(StrictModel):
    role_id: str | None = None
    disabled: bool | None = None


@router.post("/organizations", status_code=201)
def organization(
    payload: OrganizationCreate, db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "demo_admin")
    item = Organization(id=uid("organization"), **payload.model_dump())
    db.add(item)
    audit(db, "organization.created", item.id, actor)
    db.commit()
    return record(item)


@router.post("/users", status_code=201)
def user(payload: UserCreate, db=Depends(get_db), actor=Depends(get_actor)):
    permission(actor, "demo_admin")
    require(db, Organization, payload.organization_id)
    require(db, Role, payload.role_id)
    item = User(id=uid("user"), **payload.model_dump())
    db.add(item)
    audit(db, "user.created", item.id, actor, role_id=item.role_id)
    db.commit()
    return record(item)


@router.patch("/users/{user_id}")
def update(
    user_id: str, payload: UserUpdate, db=Depends(get_db), actor=Depends(get_actor)
):
    permission(actor, "demo_admin")
    from backend.services.bookings import lock_writes

    lock_writes(db)
    item = require(db, User, user_id)
    if item.id == actor.id and (
        payload.disabled or payload.role_id and payload.role_id != "admin"
    ):
        raise HTTPException(
            409,
            "Keep the current administrator enabled to avoid locking out administration.",
        )
    if payload.role_id:
        require(db, Role, payload.role_id)
        item.role_id = payload.role_id
    status = db.scalar(select(UserStatus).where(UserStatus.user_id == item.id))
    if payload.disabled is not None:
        if not status:
            status = UserStatus(id=uid("user-status"), user_id=item.id)
            db.add(status)
        status.disabled = payload.disabled
    audit(
        db,
        "user.permissions_updated",
        item.id,
        actor,
        **payload.model_dump(exclude_none=True),
    )
    db.commit()
    return {**record(item), "disabled": status.disabled if status else False}
