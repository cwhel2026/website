import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    AWAITING_PREP_BOOKING = "awaiting_prep_booking"
    BOOKED = "booked"
    PREPARATION_SCHEDULED = "preparation_scheduled"
    PREPARATION_COMPLETED = "preparation_completed"
    RESTORATION_PENDING = "restoration_pending"
    COATING_SCHEDULED = "coating_scheduled"
    COATING_COMPLETED = "coating_completed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class AppointmentType(str, enum.Enum):
    PREPARATION = "preparation"
    COATING = "coating"
    REPAIR = "repair"
    INSPECTION = "inspection"
    SINGLE_VISIT = "single_visit"


class AppointmentStatus(str, enum.Enum):
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    WEATHER_DELAYED = "weather_delayed"


class DryingStatus(str, enum.Enum):
    NOT_APPLICABLE = "not_applicable"
    AWAITING_DRY = "awaiting_dry"
    SURFACE_DRY = "surface_dry"
    INSUFFICIENT = "insufficient"
    CONFIRMED_ON_SITE = "confirmed_on_site"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE")
    )
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id"), nullable=True
    )
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_properties.id"), nullable=True
    )
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.DRAFT
    )
    requires_two_stage: Mapped[bool] = mapped_column(default=True)
    preparation_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    coating_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    seven_day_target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    drying_status: Mapped[DryingStatus] = mapped_column(
        Enum(DryingStatus, name="drying_status"), default=DryingStatus.NOT_APPLICABLE
    )
    customer_washed_already: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE")
    )
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, name="appointment_type")
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.PROVISIONAL,
    )
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(12), nullable=True)
    travel_minutes_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weather_suitable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    weather_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    job: Mapped["Job"] = relationship(back_populates="appointments")