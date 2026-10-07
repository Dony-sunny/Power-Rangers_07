from datetime import date, datetime
from typing import Literal, Annotated
from pydantic import Field, model_validator
from backend.schemas.requests import StrictModel


class PatternCreate(StrictModel):
    template_service_id: str
    name: str = Field(min_length=3, max_length=120)
    operating_days: list[int] = Field(min_length=1, max_length=7)
    departure_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    effective_date: date
    end_date: date
    capacity_tonnes: float = Field(gt=0, le=5000, allow_inf_nan=False)
    segment_capacities: dict[
        str, Annotated[float, Field(gt=0, le=5000, allow_inf_nan=False)]
    ] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ordered(self):
        if (
            self.end_date < self.effective_date
            or (self.end_date - self.effective_date).days > 90
        ):
            raise ValueError("Recurring generator limit: ordered dates within 90 days.")
        if len(set(self.operating_days)) != len(self.operating_days) or any(
            day < 0 or day > 6 for day in self.operating_days
        ):
            raise ValueError("Operating days must be unique weekday numbers 0–6.")
        self.operating_days.sort()
        return self


class RecurringBooking(StrictModel):
    cargo_id: str
    service_ids: list[str] = Field(min_length=1, max_length=12)
    contract_id: str | None = None
    approved: bool = False

    @model_validator(mode="after")
    def unique(self):
        if len(set(self.service_ids)) != len(self.service_ids):
            raise ValueError("Recurring departures must be unique.")
        return self


class ContractCreate(StrictModel):
    pattern_id: str
    start_date: date
    end_date: date
    weekly_commitment_tonnes: float = Field(gt=0, le=35000, allow_inf_nan=False)
    tonnes_per_departure: float = Field(gt=0, le=5000, allow_inf_nan=False)
    rate_per_tonne: float = Field(gt=0, le=100000, allow_inf_nan=False)
    minimum_commitment_tonnes: float = Field(ge=0, le=1000000, allow_inf_nan=False)
    start_sequence: int = Field(ge=0, le=40)
    end_sequence: int = Field(gt=0, le=40)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_date < self.start_date:
            raise ValueError("Contract end must follow start.")
        return self


class ResourceCreate(StrictModel):
    terminal_id: str
    name: str = Field(min_length=2, max_length=150)
    kind: Literal["BERTH", "CRANE", "FORKLIFT", "STORAGE", "TRUCK_GATE"]
    capacity: float = Field(gt=0, le=100000, allow_inf_nan=False)
    max_vessel_length: float = Field(default=70, gt=0, le=250, allow_inf_nan=False)


class ReservationCreate(StrictModel):
    resource_id: str
    starts_at: datetime
    ends_at: datetime
    quantity: float = Field(default=1, gt=0, le=100000, allow_inf_nan=False)
    description: str = Field(default="", max_length=250)

    @model_validator(mode="after")
    def ordered(self):
        if (
            not self.starts_at.tzinfo
            or not self.ends_at.tzinfo
            or self.ends_at <= self.starts_at
            or (self.ends_at - self.starts_at).days > 7
        ):
            raise ValueError(
                "Resource reservation requires a timezone-aware window of at most seven days."
            )
        return self


class TruckCreate(StrictModel):
    terminal_id: str
    shipment_id: str
    carrier: str = Field(min_length=2, max_length=100)
    starts_at: datetime
    ends_at: datetime
    gate_status: Literal["EXPECTED", "ARRIVED", "LOADING", "RELEASED"] = "EXPECTED"

    @model_validator(mode="after")
    def ordered(self):
        if (
            not self.starts_at.tzinfo
            or not self.ends_at.tzinfo
            or self.ends_at <= self.starts_at
        ):
            raise ValueError(
                "Truck appointment requires an ordered timezone-aware window."
            )
        return self


class FleetRequest(StrictModel):
    cargo_ids: list[str] = Field(min_length=1, max_length=40)
    vessel_ids: list[str] = Field(min_length=1, max_length=12)
    objective: Literal[
        "BALANCED", "MIN_COST", "MAX_UTILIZATION", "MIN_EMPTY", "ON_TIME"
    ] = "BALANCED"

    @model_validator(mode="after")
    def unique_inputs(self):
        if len(set(self.cargo_ids)) != len(self.cargo_ids) or len(
            set(self.vessel_ids)
        ) != len(self.vessel_ids):
            raise ValueError("Fleet cargo and vessel selections must be unique.")
        return self
