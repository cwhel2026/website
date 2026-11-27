from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.jobs import (
    AppointmentStatus,
    AppointmentType,
    DryingStatus,
    JobStatus,
)
from app.schemas.common import ORMModel


class AppointmentOut(ORMModel):
    id: UUID
    appointment_type: AppointmentType
    status: AppointmentStatus
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    travel_minutes_estimate: int | None
    weather_suitable: bool | None
    completed_at: datetime | None


class JobOut(ORMModel):
    id: UUID
    reference: str
    customer_id: UUID
    quotation_id: UUID | None
    territory_id: UUID | None
    status: JobStatus
    requires_two_stage: bool
    seven_day_target_date: date | None
    drying_status: DryingStatus
    preparation_completed_at: datetime | None
    coating_completed_at: datetime | None
    seven_day_at_risk: bool | None = None
    seven_day_message: str | None = None
    photo_count: int = 0
    appointments: list[AppointmentOut] = []


class CreateAppointmentIn(BaseModel):
    appointment_type: AppointmentType
    scheduled_start: datetime
    duration_minutes: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    postcode: str | None = None
    confirm: bool = False


class SlotProposalOut(BaseModel):
    start: datetime
    end: datetime
    appointment_type: AppointmentType
    travel_minutes: int
    weather_score: int | None
    weather_safe: bool | None


class ProposeScheduleOut(BaseModel):
    preparation_slots: list[SlotProposalOut]
    coating_slots: list[SlotProposalOut]


class CompletePrepIn(BaseModel):
    completed_at: datetime | None = None
    surface_dry_confirmed: bool = False


class FieldJobOut(BaseModel):
    job_id: UUID
    reference: str
    status: JobStatus
    postcode: str | None
    next_appointment_type: AppointmentType | None
    next_appointment_start: datetime | None
    tasks: list[str] = Field(default_factory=list)

class CompleteCoatIn(BaseModel):
    completed_at: datetime | None = None
    surface_dry_confirmed: bool
    weather_safe_confirmed: bool
