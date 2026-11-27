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
from app.models.service import SurfaceType


class SurfaceCondition(str, enum.Enum):
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    HEAVILY_DEGRADED = "heavily_degraded"


class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    PROVISIONAL = "provisional"
    PENDING_APPROVAL = "pending_approval"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Quotation(Base):
    __tablename__ = "quotations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE")
    )
    enquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enquiries.id"), nullable=True
    )
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_properties.id"), nullable=True, index=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=True
    )
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    status: Mapped[QuotationStatus] = mapped_column(
        Enum(QuotationStatus, name="quotation_status"),
        default=QuotationStatus.PROVISIONAL,
    )
    surface_type: Mapped[SurfaceType] = mapped_column(
        Enum(SurfaceType, name="surface_type", create_constraint=False)
    )
    surface_condition: Mapped[SurfaceCondition] = mapped_column(
        Enum(SurfaceCondition, name="surface_condition"),
        default=SurfaceCondition.FAIR,
    )
    requires_washing: Mapped[bool] = mapped_column(default=True)
    customer_washed_already: Mapped[bool] = mapped_column(default=False)
    total_area_sqm: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    pricing_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pricing_profiles.id"), nullable=True
    )
    subtotal_ex_vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_inc_vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Frozen on the day the quote was priced. Later registration changes do not rewrite it.
    vat_charged: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    estimated_labour_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    estimated_materials_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estimated_travel_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estimated_contribution_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    meets_minimum_margin: Mapped[bool] = mapped_column(default=True)
    requires_approval: Mapped[bool] = mapped_column(default=False)
    provisional_disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Provisional price subject to on-site measurement and condition verification.",
    )
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sections: Mapped[list["QuotationSection"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    calculations: Mapped[list["QuotationCalculation"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )


class QuotationSection(Base):
    __tablename__ = "quotation_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(120), default="Main area")
    length_m: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    width_m: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    quotation: Mapped["Quotation"] = relationship(back_populates="sections")


class QuotationCalculation(Base):
    """Versioned line-item breakdown for audit."""

    __tablename__ = "quotation_calculations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="CASCADE")
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    breakdown_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    quotation: Mapped["Quotation"] = relationship(back_populates="calculations")