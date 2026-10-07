from sqlalchemy import ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base
from backend.models.domain import Identified, now_iso


class BulkImport(Identified, Base):
    __tablename__ = "bulk_imports"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    rows: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now_iso)
    imported: Mapped[bool] = mapped_column(default=False)


class UserStatus(Identified, Base):
    __tablename__ = "user_status"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    disabled: Mapped[bool] = mapped_column(default=False)


class EvidencePhoto(Identified, Base):
    __tablename__ = "evidence_photos"
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str]
    description: Mapped[str]
    image_base64: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now_iso)


class LabelReference(Identified, Base):
    __tablename__ = "label_references"
    entity_type: Mapped[str]
    entity_id: Mapped[str]
    __table_args__ = (UniqueConstraint("entity_type", "entity_id"),)


class DeliveryChallenge(Identified, Base):
    __tablename__ = "delivery_challenges"
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"))
    receiver_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    salt: Mapped[str]
    otp_hash: Mapped[str]
    expires_at: Mapped[str]
    attempts: Mapped[int] = mapped_column(default=0)
    verified_at: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(default=now_iso)


class ServicePattern(Identified, Base):
    __tablename__ = "service_patterns"
    name: Mapped[str]
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    operating_days: Mapped[list] = mapped_column(JSON)
    departure_time: Mapped[str]
    effective_date: Mapped[str]
    end_date: Mapped[str]
    capacity_tonnes: Mapped[float]
    segment_capacities: Mapped[dict] = mapped_column(JSON)
    stops: Mapped[list] = mapped_column(JSON)
    vessel_class: Mapped[str]
    status: Mapped[str] = mapped_column(default="ACTIVE")


class ServiceOccurrence(Identified, Base):
    __tablename__ = "service_occurrences"
    __table_args__ = (UniqueConstraint("pattern_id", "operating_date"),)
    pattern_id: Mapped[str] = mapped_column(ForeignKey("service_patterns.id"))
    service_id: Mapped[str] = mapped_column(
        ForeignKey("scheduled_services.id"), unique=True
    )
    operating_date: Mapped[str]
    status: Mapped[str] = mapped_column(default="SCHEDULED")


class CapacityContract(Identified, Base):
    __tablename__ = "capacity_contracts"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    pattern_id: Mapped[str] = mapped_column(ForeignKey("service_patterns.id"))
    start_date: Mapped[str]
    end_date: Mapped[str]
    weekly_commitment_tonnes: Mapped[float]
    tonnes_per_departure: Mapped[float]
    rate_per_tonne: Mapped[float]
    minimum_commitment_tonnes: Mapped[float]
    start_sequence: Mapped[int]
    end_sequence: Mapped[int]
    status: Mapped[str] = mapped_column(default="ACTIVE")


class ContractReservation(Identified, Base):
    __tablename__ = "contract_reservations"
    contract_id: Mapped[str] = mapped_column(ForeignKey("capacity_contracts.id"))
    service_id: Mapped[str] = mapped_column(ForeignKey("scheduled_services.id"))
    tonnes: Mapped[float]
    __table_args__ = (UniqueConstraint("contract_id", "service_id"),)


class ContractDraw(Identified, Base):
    __tablename__ = "contract_draws"
    contract_id: Mapped[str] = mapped_column(ForeignKey("capacity_contracts.id"))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True)
    service_id: Mapped[str] = mapped_column(ForeignKey("scheduled_services.id"))
    tonnes: Mapped[float]


class TerminalResource(Identified, Base):
    __tablename__ = "terminal_resources"
    terminal_id: Mapped[str] = mapped_column(ForeignKey("terminals.id"))
    name: Mapped[str]
    kind: Mapped[str]
    capacity: Mapped[float] = mapped_column(default=1)
    max_vessel_length: Mapped[float] = mapped_column(default=70)
    active: Mapped[bool] = mapped_column(default=True)


class ResourceReservation(Identified, Base):
    __tablename__ = "resource_reservations"
    resource_id: Mapped[str] = mapped_column(ForeignKey("terminal_resources.id"))
    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"))
    starts_at: Mapped[str]
    ends_at: Mapped[str]
    quantity: Mapped[float] = mapped_column(default=1)
    description: Mapped[str] = mapped_column(default="")


class TruckAppointment(Identified, Base):
    __tablename__ = "truck_appointments"
    terminal_id: Mapped[str] = mapped_column(ForeignKey("terminals.id"))
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"))
    carrier: Mapped[str]
    starts_at: Mapped[str]
    ends_at: Mapped[str]
    gate_status: Mapped[str] = mapped_column(default="EXPECTED")


class FleetAssignmentPlan(Identified, Base):
    __tablename__ = "fleet_assignment_plans"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    result: Mapped[dict] = mapped_column(JSON)
    approved: Mapped[bool] = mapped_column(default=False)


class DisruptionRecord(Identified, Base):
    __tablename__ = "disruption_records"
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"))
    kind: Mapped[str]
    detail: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now_iso)


class DemandSearch(Identified, Base):
    __tablename__ = "demand_searches"
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    outcome: Mapped[str]
    reasons: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now_iso)


class FreightRateObservation(Identified, Base):
    __tablename__ = "freight_rate_observations"
    origin: Mapped[str]
    destination: Mapped[str]
    cargo_class: Mapped[str]
    weight_tonnes: Mapped[float]
    rate_per_tonne: Mapped[float]
    observed_at: Mapped[str]
    source: Mapped[str]


class NavigationPhoto(Identified, Base):
    __tablename__ = "navigation_photos"
    report_id: Mapped[str] = mapped_column(ForeignKey("navigation_reports.id"))
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    image_base64: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(default=now_iso)


class JudgeSession(Identified, Base):
    __tablename__ = "judge_sessions"
    state: Mapped[dict] = mapped_column(JSON, default=dict)
