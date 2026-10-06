from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class Identified:
    id: Mapped[str] = mapped_column(String(80), primary_key=True)


class Organization(Identified, Base):
    __tablename__ = "organizations"
    name: Mapped[str]
    kind: Mapped[str]
    verified: Mapped[bool] = mapped_column(default=False)


class Role(Identified, Base):
    __tablename__ = "roles"
    label: Mapped[str]
    permissions: Mapped[list] = mapped_column(JSON, default=list)


class User(Identified, Base):
    __tablename__ = "users"
    name: Mapped[str]
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"))


class CargoRequest(Identified, Base):
    __tablename__ = "cargo_requests"
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    cargo_type: Mapped[str]
    weight_tonnes: Mapped[float]
    volume_m3: Mapped[float | None]
    packaging: Mapped[str]
    fragile: Mapped[bool] = mapped_column(default=False)
    perishable: Mapped[bool] = mapped_column(default=False)
    hazardous: Mapped[bool] = mapped_column(default=False)
    temperature_control_required: Mapped[bool] = mapped_column(default=False)
    origin: Mapped[str]
    destination: Mapped[str]
    origin_coordinates: Mapped[list | None] = mapped_column(JSON)
    destination_coordinates: Mapped[list | None] = mapped_column(JSON)
    ready_time: Mapped[str]
    delivery_deadline: Mapped[str]
    first_mile_required: Mapped[bool] = mapped_column(default=True)
    last_mile_required: Mapped[bool] = mapped_column(default=True)
    consolidation_allowed: Mapped[bool] = mapped_column(default=True)
    prohibited_co_load_categories: Mapped[list] = mapped_column(JSON, default=list)
    budget: Mapped[float | None]
    priority: Mapped[str] = mapped_column(default="NORMAL")
    status: Mapped[str] = mapped_column(default="POSTED")
    created_at: Mapped[str] = mapped_column(default=now_iso)


class CargoDocument(Identified, Base):
    __tablename__ = "cargo_documents"
    cargo_id: Mapped[str | None] = mapped_column(ForeignKey("cargo_requests.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    filename: Mapped[str]
    mime_type: Mapped[str]
    extracted_text: Mapped[str] = mapped_column(Text)
    extraction: Mapped[dict] = mapped_column(JSON)


class CargoPreference(Identified, Base):
    __tablename__ = "cargo_preferences"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    preferred_operators: Mapped[list] = mapped_column(JSON, default=list)
    ranking_profile: Mapped[str] = mapped_column(default="BALANCED")
    recurring_contract: Mapped[dict] = mapped_column(JSON, default=dict)


class Vessel(Identified, Base):
    __tablename__ = "vessels"
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str]
    vessel_type: Mapped[str] = mapped_column(default="BARGE")
    max_capacity_tonnes: Mapped[float]
    max_volume_m3: Mapped[float]
    length: Mapped[float]
    beam: Mapped[float]
    loaded_draft: Mapped[float]
    air_draft: Mapped[float]
    current_location: Mapped[str]
    cargo_categories: Mapped[list] = mapped_column(JSON)
    maintenance_status: Mapped[str] = mapped_column(default="OPERATIONAL")
    compliance_status: Mapped[str] = mapped_column(default="PASS")
    reliability_score: Mapped[float] = mapped_column(default=0.9)
    rate_per_tonne_km: Mapped[float] = mapped_column(default=3.2)
    cold_chain: Mapped[bool] = mapped_column(default=False)
    hazardous_certified: Mapped[bool] = mapped_column(default=False)
    state: Mapped[str] = mapped_column(default="AVAILABLE")
    trust_metrics: Mapped[dict] = mapped_column(JSON, default=dict)


class VesselAvailability(Identified, Base):
    __tablename__ = "vessel_availability"
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"), index=True)
    origin: Mapped[str]
    destination: Mapped[str]
    available_from: Mapped[str]
    available_until: Mapped[str]
    capacity_tonnes: Mapped[float]
    volume_m3: Mapped[float]
    active: Mapped[bool] = mapped_column(default=True)


class VesselCertificate(Identified, Base):
    __tablename__ = "vessel_certificates"
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    kind: Mapped[str]
    expires_at: Mapped[str]
    verified: Mapped[bool] = mapped_column(default=False)


class VesselMaintenanceStatus(Identified, Base):
    __tablename__ = "vessel_maintenance"
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    status: Mapped[str]
    defect: Mapped[str] = mapped_column(default="")
    inspection_date: Mapped[str | None]
    due_date: Mapped[str | None]
    return_to_service: Mapped[str | None]


class WaterwayNode(Identified, Base):
    __tablename__ = "waterway_nodes"
    name: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]


class WaterwaySegment(Identified, Base):
    __tablename__ = "waterway_segments"
    source_node: Mapped[str] = mapped_column(ForeignKey("waterway_nodes.id"))
    destination_node: Mapped[str] = mapped_column(ForeignKey("waterway_nodes.id"))
    distance_km: Mapped[float]
    available_depth: Mapped[float]
    minimum_width: Mapped[float]
    minimum_bridge_clearance: Mapped[float]
    lock_required: Mapped[bool] = mapped_column(default=False)
    lock_name: Mapped[str | None]
    lock_open_hour: Mapped[int] = mapped_column(default=0)
    lock_close_hour: Mapped[int] = mapped_column(default=24)
    navigation_status: Mapped[str] = mapped_column(default="OPEN")
    restriction: Mapped[str | None]
    source_name: Mapped[str] = mapped_column(default="Synthetic hackathon fixture")
    source_date: Mapped[str]
    confidence: Mapped[str] = mapped_column(default="DEMO")
    last_verified: Mapped[str | None]
    verification_status: Mapped[str] = mapped_column(default="SIMULATED")


class RouteRestriction(Identified, Base):
    __tablename__ = "route_restrictions"
    segment_id: Mapped[str] = mapped_column(ForeignKey("waterway_segments.id"))
    reason: Mapped[str]
    starts_at: Mapped[str]
    ends_at: Mapped[str]
    status: Mapped[str] = mapped_column(default="ACTIVE")


class NavigationReport(Identified, Base):
    __tablename__ = "navigation_reports"
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    segment_id: Mapped[str] = mapped_column(ForeignKey("waterway_segments.id"))
    report_type: Mapped[str]
    description: Mapped[str]
    coordinates: Mapped[list] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(default=0.5)
    verification_status: Mapped[str] = mapped_column(default="UNVERIFIED")
    created_at: Mapped[str] = mapped_column(default=now_iso)
    expires_at: Mapped[str]


class Terminal(Identified, Base):
    __tablename__ = "terminals"
    node_id: Mapped[str] = mapped_column(ForeignKey("waterway_nodes.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str]
    handling_rate: Mapped[float]
    wait_hours: Mapped[float]
    source_name: Mapped[str]
    source_date: Mapped[str]
    verification_status: Mapped[str] = mapped_column(default="SIMULATED")


class TerminalCapability(Identified, Base):
    __tablename__ = "terminal_capabilities"
    terminal_id: Mapped[str] = mapped_column(ForeignKey("terminals.id"), unique=True)
    cargo_types: Mapped[list] = mapped_column(JSON)
    jetty_length: Mapped[float]
    available_storage: Mapped[float]
    covered_storage: Mapped[bool]
    crane_available: Mapped[bool]
    crane_capacity: Mapped[float]
    forklift_available: Mapped[bool]
    forklift_capacity: Mapped[float]
    road_access: Mapped[bool]
    approach_channel: Mapped[float]
    operational_status: Mapped[str] = mapped_column(default="OPEN")


class TerminalSlot(Identified, Base):
    __tablename__ = "terminal_slots"
    terminal_id: Mapped[str] = mapped_column(ForeignKey("terminals.id"))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"))
    starts_at: Mapped[str]
    ends_at: Mapped[str]
    operation: Mapped[str]


class TransportQuote(Identified, Base):
    __tablename__ = "transport_quotes"
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    vessel_id: Mapped[str | None] = mapped_column(ForeignKey("vessels.id"))
    mode: Mapped[str]
    total: Mapped[float]
    breakdown: Mapped[dict] = mapped_column(JSON)
    eta: Mapped[str]
    reliability: Mapped[float]
    created_at: Mapped[str] = mapped_column(default=now_iso)


class MatchRecommendation(Identified, Base):
    __tablename__ = "match_recommendations"
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    passed: Mapped[bool]
    score: Mapped[float]
    explanation: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now_iso)


class PoolingGroup(Identified, Base):
    __tablename__ = "pooling_groups"
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    cargo_ids: Mapped[list] = mapped_column(JSON)
    total_tonnes: Mapped[float]
    utilization: Mapped[float]
    solver_status: Mapped[str]


class BackhaulOpportunity(Identified, Base):
    __tablename__ = "backhaul_opportunities"
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    outbound_cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    revenue: Mapped[float]
    departure: Mapped[str]


class ScheduledService(Identified, Base):
    __tablename__ = "scheduled_services"
    name: Mapped[str]
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    departure: Mapped[str]
    capacity_tonnes: Mapped[float]
    recurrence: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)


class ScheduledServiceStop(Identified, Base):
    __tablename__ = "scheduled_service_stops"
    service_id: Mapped[str] = mapped_column(ForeignKey("scheduled_services.id"))
    terminal_id: Mapped[str] = mapped_column(ForeignKey("terminals.id"))
    sequence: Mapped[int]
    arrival: Mapped[str]
    departure: Mapped[str]


class ScheduledCapacityBooking(Identified, Base):
    __tablename__ = "scheduled_capacity_bookings"
    __table_args__ = (UniqueConstraint("service_id", "cargo_id"),)
    service_id: Mapped[str] = mapped_column(ForeignKey("scheduled_services.id"))
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"))
    weight_tonnes: Mapped[float]
    start_sequence: Mapped[int]
    end_sequence: Mapped[int]


class Booking(Identified, Base):
    __tablename__ = "bookings"
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"), index=True)
    vessel_id: Mapped[str | None] = mapped_column(ForeignKey("vessels.id"))
    availability_id: Mapped[str | None] = mapped_column(
        ForeignKey("vessel_availability.id")
    )
    origin_terminal_id: Mapped[str | None] = mapped_column(ForeignKey("terminals.id"))
    destination_terminal_id: Mapped[str | None] = mapped_column(
        ForeignKey("terminals.id")
    )
    mode: Mapped[str]
    status: Mapped[str] = mapped_column(default="CONFIRMED")
    total_cost: Mapped[float]
    cost_breakdown: Mapped[dict] = mapped_column(JSON)
    departure: Mapped[str]
    eta: Mapped[str]
    risk: Mapped[dict] = mapped_column(JSON)
    plan_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    pool_id: Mapped[str | None] = mapped_column(ForeignKey("pooling_groups.id"))
    created_at: Mapped[str] = mapped_column(default=now_iso)


class Shipment(Identified, Base):
    __tablename__ = "shipments"
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True)
    status: Mapped[str] = mapped_column(default="CONFIRMED")
    progress: Mapped[float] = mapped_column(default=0)
    latitude: Mapped[float]
    longitude: Mapped[float]
    operational_data: Mapped[dict] = mapped_column(JSON, default=dict)


class ShipmentLeg(Identified, Base):
    __tablename__ = "shipment_legs"
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"))
    mode: Mapped[str]
    origin: Mapped[str]
    destination: Mapped[str]
    sequence: Mapped[int]
    assigned_provider: Mapped[str | None]


class TrackingEvent(Identified, Base):
    __tablename__ = "tracking_events"
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"))
    status: Mapped[str]
    description: Mapped[str]
    timestamp: Mapped[str] = mapped_column(default=now_iso)
    latitude: Mapped[float]
    longitude: Mapped[float]
    simulated: Mapped[bool] = mapped_column(default=True)


class InvoiceRecord(Identified, Base):
    __tablename__ = "invoices"
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True)
    total: Mapped[float]
    status: Mapped[str] = mapped_column(default="DRAFT")
    line_items: Mapped[dict] = mapped_column(JSON)


class PaymentRecord(Identified, Base):
    __tablename__ = "payments"
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), unique=True)
    status: Mapped[str] = mapped_column(default="PENDING")
    amount: Mapped[float]
    operator_payout: Mapped[float]
    dispute: Mapped[str | None]


class ComplianceCheck(Identified, Base):
    __tablename__ = "compliance_checks"
    vessel_id: Mapped[str] = mapped_column(ForeignKey("vessels.id"))
    cargo_id: Mapped[str] = mapped_column(ForeignKey("cargo_requests.id"))
    passed: Mapped[bool]
    reasons: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now_iso)


class ImpactMetric(Identified, Base):
    __tablename__ = "impact_metrics"
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True)
    tonnes_shifted: Mapped[float]
    road_baseline_cost: Mapped[float]
    chosen_cost: Mapped[float]
    road_emissions_kg: Mapped[float]
    chosen_emissions_kg: Mapped[float]
    truck_trips_avoided: Mapped[int]
    utilization_before: Mapped[float]
    utilization_after: Mapped[float]
    empty_return_avoided: Mapped[bool] = mapped_column(default=False)


class AuditEvent(Identified, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str | None]
    organization_id: Mapped[str | None]
    event: Mapped[str]
    entity_id: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[str] = mapped_column(default=now_iso)
