from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CargoCreate(StrictModel):
    cargo_type: str = Field(min_length=2, max_length=80)
    weight_tonnes: float = Field(gt=0, le=10000, allow_inf_nan=False)
    volume_m3: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    packaging: str = Field(min_length=2, max_length=80)
    origin: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    origin_coordinates: tuple[float, float] | None = None
    destination_coordinates: tuple[float, float] | None = None
    ready_time: datetime
    delivery_deadline: datetime
    fragile: bool = False
    perishable: bool = False
    hazardous: bool = False
    temperature_control_required: bool = False
    first_mile_required: bool = True
    last_mile_required: bool = True
    consolidation_allowed: bool = True
    prohibited_co_load_categories: list[str] = Field(
        default_factory=list, max_length=30
    )
    budget: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    priority: Literal["NORMAL", "URGENT", "CRITICAL"] = "NORMAL"

    @model_validator(mode="after")
    def validate_window(self):
        if self.ready_time.tzinfo is None or self.delivery_deadline.tzinfo is None:
            raise ValueError("Use timestamps with timezone offsets.")
        if self.delivery_deadline <= self.ready_time:
            raise ValueError("Delivery deadline must follow cargo readiness.")
        if self.origin.casefold() == self.destination.casefold():
            raise ValueError("Origin and destination must differ.")
        for coords in (self.origin_coordinates, self.destination_coordinates):
            if coords and not (-90 <= coords[0] <= 90 and -180 <= coords[1] <= 180):
                raise ValueError("Coordinates outside latitude/longitude bounds.")
        return self


class VesselCreate(StrictModel):
    name: str = Field(min_length=2, max_length=100)
    vessel_type: str = "BARGE"
    max_capacity_tonnes: float = Field(gt=0, le=5000, allow_inf_nan=False)
    max_volume_m3: float = Field(gt=0, le=20000, allow_inf_nan=False)
    length: float = Field(gt=0, le=250, allow_inf_nan=False)
    beam: float = Field(gt=0, le=50, allow_inf_nan=False)
    loaded_draft: float = Field(gt=0, le=20, allow_inf_nan=False)
    air_draft: float = Field(gt=0, le=50, allow_inf_nan=False)
    current_location: str
    cargo_categories: list[str] = Field(min_length=1, max_length=40)
    rate_per_tonne_km: float = Field(default=3.2, gt=0, le=500, allow_inf_nan=False)
    cold_chain: bool = False
    hazardous_certified: bool = False


class AvailabilityDetails(StrictModel):
    origin: str
    destination: str
    available_from: datetime
    available_until: datetime
    capacity_tonnes: float = Field(gt=0, allow_inf_nan=False)
    volume_m3: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def window(self):
        if (
            self.available_from.tzinfo is None
            or self.available_until.tzinfo is None
            or self.available_until <= self.available_from
        ):
            raise ValueError("Availability requires an ordered timezone-aware window.")
        if self.origin.casefold() == self.destination.casefold():
            raise ValueError("Availability endpoints must differ.")
        return self


class AvailabilityCreate(AvailabilityDetails):
    vessel_id: str


class VesselListing(StrictModel):
    vessel: VesselCreate
    availability: AvailabilityDetails
    demo_certificate_review: bool = False


class TextIntake(StrictModel):
    text: str = Field(min_length=3, max_length=30000)


class BookingCreate(StrictModel):
    cargo_id: str
    vessel_id: str | None = None
    mode: Literal["ROAD", "WATER", "HYBRID"] = "HYBRID"
    pool_id: str | None = None
    service_id: str | None = None
    contract_id: str | None = None
    approved: bool = False


class StateChange(StrictModel):
    status: Literal[
        "SCHEDULED",
        "LOADING",
        "IN_TRANSIT",
        "UNLOADING",
        "LAST_MILE",
        "DELIVERED",
        "CANCELLED",
        "FAILED",
        "REPLANNING",
    ]


class Disruption(StrictModel):
    kind: Literal[
        "VESSEL_UNAVAILABLE",
        "ROUTE_CLOSED",
        "TERMINAL_CLOSED",
        "EQUIPMENT_UNAVAILABLE",
        "SHIPMENT_NOT_READY",
        "TRUCK_LATE",
        "SERVICE_CANCELLED",
        "CAPACITY_REDUCED",
    ]
    delay_minutes: int = Field(default=60, ge=0, le=1440)
    capacity_tonnes: float | None = Field(
        default=None, gt=0, le=5000, allow_inf_nan=False
    )


class RecoveryApproval(StrictModel):
    vessel_id: str | None = None
    mode: Literal["ROAD", "WATER", "HYBRID"] = "HYBRID"
    approved: bool = False
    service_id: str | None = None


class OperationUpdate(StrictModel):
    actual_weight_tonnes: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    actual_volume_m3: float | None = Field(
        default=None, gt=0, le=100000, allow_inf_nan=False
    )
    packing_ready: bool | None = None
    truck_assignment: str | None = Field(default=None, max_length=100)
    handover_confirmed: bool | None = None
    quantity_received_tonnes: float | None = Field(
        default=None, ge=0, allow_inf_nan=False
    )
    damage_report: str | None = Field(default=None, max_length=2000)
    delivery_signature: str | None = Field(default=None, max_length=100)
    gate_out: bool | None = None
    loading_sequence: list[str] | None = Field(default=None, max_length=30)
    crew_assignment: str | None = Field(default=None, max_length=200)
    handling_completed: bool | None = None
    terminal_delay_minutes: int | None = Field(default=None, ge=0, le=1440)


class NavigationCreate(StrictModel):
    segment_id: str
    report_type: Literal[
        "VEGETATION", "SHALLOW", "OBSTRUCTION", "DEBRIS", "DELAY", "HAZARD", "OTHER"
    ]
    description: str = Field(min_length=3, max_length=2000)
    coordinates: tuple[float, float]
    confidence: float = Field(default=0.5, ge=0, le=1, allow_inf_nan=False)


class MaintenanceUpdate(StrictModel):
    status: Literal["OPERATIONAL", "MAINTENANCE", "DEFECT"]
    defect: str = Field(default="", max_length=2000)


class PaymentUpdate(StrictModel):
    status: Literal["PENDING", "PAID", "DISPUTED", "SETTLED"]
    dispute: str | None = Field(default=None, max_length=2000)
