import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WorkActivity(str, enum.Enum):
    WASHING = "washing"
    COATING = "coating"
    REPAIR = "repair"


class ProductProfile(Base):
    """Configurable product application limits — not manufacturer-certified until documented."""

    __tablename__ = "product_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    min_application_temp_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10"))
    max_application_temp_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("28"))
    min_drying_hours: Mapped[int] = mapped_column(Integer, default=24)
    rain_free_window_hours: Mapped[int] = mapped_column(Integer, default=4)
    max_wind_mph: Mapped[int] = mapped_column(Integer, default=20)
    documentation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WeatherForecastHour(Base):
    """Cached hourly forecast row (simulated or live provider)."""

    __tablename__ = "weather_forecast_hours"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    temp_c: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    precipitation_mm: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"))
    precip_probability_pct: Mapped[int] = mapped_column(Integer, default=0)
    wind_mph: Mapped[int] = mapped_column(Integer, default=0)
    humidity_pct: Mapped[int] = mapped_column(Integer, default=50)
    source: Mapped[str] = mapped_column(String(40), default="simulation")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AppointmentWeatherCheck(Base):
    __tablename__ = "appointment_weather_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE")
    )
    activity: Mapped[WorkActivity] = mapped_column(Enum(WorkActivity, name="work_activity"))
    suitability_score: Mapped[int] = mapped_column(Integer)
    is_safe: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_on_site_confirmation: Mapped[bool] = mapped_column(default=True)
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )