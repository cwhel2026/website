import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


class MarketingExperiment(Base):
    __tablename__ = "marketing_experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200))
    hypothesis: Mapped[str] = mapped_column(Text)
    variant_a: Mapped[str] = mapped_column(Text)
    variant_b: Mapped[str] = mapped_column(Text)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name="experiment_status"), default=ExperimentStatus.DRAFT
    )
    spend_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    enquiries: Mapped[int] = mapped_column(default=0)
    quotations: Mapped[int] = mapped_column(default=0)
    bookings: Mapped[int] = mapped_column(default=0)
    revenue_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )