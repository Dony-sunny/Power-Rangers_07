"""Additive Cargo Lines schema; existing bookings and databases remain readable."""
from sqlalchemy import ForeignKey, JSON, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base
from backend.models.domain import Identified, now_iso


class CoordinationGrant(Identified, Base):
    __tablename__ = "coordination_grants"
    owner_org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    coordinator_org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    __table_args__ = (UniqueConstraint("owner_org_id", "coordinator_org_id"),)


class CargoLoadProfile(Identified, Base):
    __tablename__ = "cargo_load_profiles"
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"), unique=True)
    heaviest_piece_tonnes: Mapped[float]
    unit_length_m: Mapped[float] = mapped_column(default=1)
    unit_width_m: Mapped[float] = mapped_column(default=1)
    unit_height_m: Mapped[float] = mapped_column(default=1)
    pieces: Mapped[int] = mapped_column(default=1)
    receiving_from: Mapped[str | None]
    receiving_until: Mapped[str | None]


class TerminalRateCard(Identified, Base):
    __tablename__ = "terminal_rate_cards"
    terminal_id: Mapped[str] = mapped_column(ForeignKey("terminals.id"))
    version: Mapped[int]
    terms: Mapped[dict] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(default="SIMULATED")
    created_at: Mapped[str] = mapped_column(default=now_iso)
    __table_args__ = (UniqueConstraint("terminal_id", "version"),)


class TruckResource(Identified, Base):
    __tablename__ = "truck_resources"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str]
    payload_tonnes: Mapped[float] = mapped_column(default=20)
    volume_m3: Mapped[float] = mapped_column(default=60)
    unit_length_m: Mapped[float] = mapped_column(default=6)
    unit_width_m: Mapped[float] = mapped_column(default=2.4)
    unit_height_m: Mapped[float] = mapped_column(default=2.5)
    pieces_per_trip: Mapped[int] = mapped_column(default=2000)
    cargo_categories: Mapped[list] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(default=True)


class CargoVoyage(Identified, Base):
    __tablename__ = "cargo_voyages"
    coordinator_org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    dispatcher_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    vessel_id: Mapped[str | None] = mapped_column(ForeignKey("vessels.id"))
    version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(default="HELD")
    plan: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[str]
    cutoff: Mapped[str]
    operator_accepted_version: Mapped[int | None]
    operator_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("cargo_voyages.id"))
    created_at: Mapped[str] = mapped_column(default=now_iso)


class LineQuote(Identified, Base):
    __tablename__ = "line_quotes"
    voyage_id: Mapped[str] = mapped_column(ForeignKey("cargo_voyages.id"))
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    cargo_revision: Mapped[str]
    total_minor: Mapped[int]
    snapshot: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now_iso)
    __table_args__ = (UniqueConstraint("voyage_id", "cargo_id"),)


class QuoteAcceptance(Identified, Base):
    __tablename__ = "quote_acceptances"
    quote_id: Mapped[str] = mapped_column(ForeignKey("line_quotes.id"), unique=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    accepted_at: Mapped[str] = mapped_column(default=now_iso)


class VoyageMember(Identified, Base):
    __tablename__ = "voyage_members"
    voyage_id: Mapped[str] = mapped_column(ForeignKey("cargo_voyages.id"))
    quote_id: Mapped[str] = mapped_column(ForeignKey("line_quotes.id"), unique=True)
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"), index=True)
    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"), unique=True)
    status: Mapped[str] = mapped_column(default="PROPOSED")
    receipt: Mapped[dict | None] = mapped_column(JSON)


class ProviderJob(Identified, Base):
    __tablename__ = "provider_jobs"
    voyage_id: Mapped[str] = mapped_column(ForeignKey("cargo_voyages.id"), index=True)
    cargo_id: Mapped[str | None] = mapped_column(ForeignKey("cargo_requests.id"))
    provider_org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    terminal_resource_id: Mapped[str | None] = mapped_column(ForeignKey("terminal_resources.id"))
    truck_resource_id: Mapped[str | None] = mapped_column(ForeignKey("truck_resources.id"))
    kind: Mapped[str]
    quantity: Mapped[float] = mapped_column(default=1)
    starts_at: Mapped[str]
    ends_at: Mapped[str]
    status: Mapped[str] = mapped_column(default="PENDING")
    expires_at: Mapped[str]
    provider_reference: Mapped[str | None]
    source: Mapped[str] = mapped_column(default="SIMULATED")
    responded_at: Mapped[str | None]


def immutable_record(mapper, connection, target):
    raise ValueError("Quote versions and rate cards are immutable; create a new version.")


event.listen(LineQuote, "before_update", immutable_record)
event.listen(TerminalRateCard, "before_update", immutable_record)
