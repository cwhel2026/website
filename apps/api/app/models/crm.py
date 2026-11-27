import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.service import SurfaceType


class PipelineStage(str, enum.Enum):
    NEW_ENQUIRY = "new_enquiry"
    AWAITING_INFORMATION = "awaiting_information"
    AWAITING_PHOTOGRAPHS = "awaiting_photographs"
    QUOTE_GENERATED = "quote_generated"
    QUOTE_SENT = "quote_sent"
    QUOTE_ACCEPTED = "quote_accepted"
    REGIONAL_WAITING_LIST = "regional_waiting_list"
    BOOKING_PENDING = "booking_pending"
    BOOKED = "booked"
    WASHING_COMPLETED = "washing_completed"
    RESTORATION_PENDING = "restoration_pending"
    JOB_COMPLETED = "job_completed"
    INVOICED = "invoiced"
    PAID = "paid"
    REVIEW_REQUESTED = "review_requested"
    REPEAT_CUSTOMER = "repeat_customer"
    CANCELLED_OR_LOST = "cancelled_or_lost"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200))
    consent_marketing: Mapped[bool] = mapped_column(default=False)
    consent_service_messages: Mapped[bool] = mapped_column(default=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    properties: Mapped[list["CustomerProperty"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    enquiries: Mapped[list["Enquiry"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class CustomerProperty(Base):
    __tablename__ = "customer_properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE")
    )
    address_line1: Mapped[str] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    town: Mapped[str] = mapped_column(String(120))
    postcode: Mapped[str] = mapped_column(String(12), index=True)
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="properties")


class Enquiry(Base):
    __tablename__ = "enquiries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE")
    )
    stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage, name="pipeline_stage"), default=PipelineStage.NEW_ENQUIRY
    )
    surface_type: Mapped[SurfaceType | None] = mapped_column(
        Enum(SurfaceType, name="surface_type", create_constraint=False),
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_properties.id"), nullable=True, index=True
    )
    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship(back_populates="enquiries")