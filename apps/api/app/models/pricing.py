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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.service import ServiceCategory, SurfaceType


class PricingRuleType(str, enum.Enum):
    PER_SQM = "per_sqm"
    MINIMUM_JOB = "minimum_job"
    WASHING_SURCHARGE = "washing_surcharge"
    COATING_SURCHARGE = "coating_surcharge"
    REPAIR_UNIT = "repair_unit"
    TRAVEL = "travel"
    COMMERCIAL_MULTIPLIER = "commercial_multiplier"
    CONDITION_SURCHARGE = "condition_surcharge"
    VAT_RATE = "vat_rate"
    MIN_CONTRIBUTION_MARGIN = "min_contribution_margin"


class PricingProfile(Base):
    """Versioned pricing configuration; quotations reference a profile version."""

    __tablename__ = "pricing_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), default="default")
    version: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    rules: Mapped[list["PricingRule"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pricing_profiles.id", ondelete="CASCADE")
    )
    rule_type: Mapped[PricingRuleType] = mapped_column(
        Enum(PricingRuleType, name="pricing_rule_type")
    )
    service_category: Mapped[ServiceCategory | None] = mapped_column(
        Enum(ServiceCategory, name="service_category", create_constraint=False),
        nullable=True,
    )
    surface_type: Mapped[SurfaceType | None] = mapped_column(
        Enum(SurfaceType, name="surface_type", create_constraint=False),
        nullable=True,
    )
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    # Distinguishes launch vs standard per-m² rates. Null means the rule applies to every tier.
    label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    profile: Mapped["PricingProfile"] = relationship(back_populates="rules")