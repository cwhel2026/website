import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SchedulingSettings(Base):
    """Singleton-style owner scheduling constraints (id fixed in seed)."""

    __tablename__ = "scheduling_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), default=Decimal("53.5977"))
    base_longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), default=Decimal("-2.8407"))
    base_label: Mapped[str] = mapped_column(String(120), default="Burscough HQ")
    max_daily_driving_minutes: Mapped[int] = mapped_column(Integer, default=180)
    max_job_distance_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("80"))
    max_daily_working_hours: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("9"))
    travel_buffer_minutes: Mapped[int] = mapped_column(Integer, default=15)
    default_prep_duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    default_coat_duration_minutes: Mapped[int] = mapped_column(Integer, default=150)
    min_drying_hours: Mapped[int] = mapped_column(Integer, default=24)
    seven_day_coating_target_days: Mapped[int] = mapped_column(Integer, default=7)
    work_day_start: Mapped[time] = mapped_column(Time, default=time(8, 0))
    work_day_end: Mapped[time] = mapped_column(Time, default=time(17, 30))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OwnerCalendarBlock(Base):
    __tablename__ = "owner_calendar_blocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(160))
    block_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    block_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_unavailable: Mapped[bool] = mapped_column(default=True)
    source: Mapped[str] = mapped_column(String(40), default="internal")


class RegionalWorkingDay(Base):
    __tablename__ = "regional_working_days"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id", ondelete="CASCADE")
    )
    work_date: Mapped[date] = mapped_column(Date)
    focus: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)