"""Private driveway photographs attached to a quotation.

Photographs are never approved for marketing from this flow. A future job sheet
reaches them through quotation_id. The provisional price is not stored here.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuotePhotoSet(Base):
    __tablename__ = "quote_photo_sets"
    __table_args__ = (
        UniqueConstraint("token", name="uq_quote_photo_sets_token"),
        Index("ix_quote_photo_sets_quotation_id", "quotation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(String(80), nullable=False)
    customer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True
    )
    enquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enquiries.id", ondelete="SET NULL"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_properties.id", ondelete="SET NULL"), nullable=True
    )
    marketing_use_allowed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    ai_status: Mapped[str] = mapped_column(String(40), default="pending", server_default=text("'pending'"))
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    review_status: Mapped[str] = mapped_column(
        String(40), default="not_required", server_default=text("'not_required'")
    )
    repair_price_gbp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    repair_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    photos: Mapped[list["QuotePhoto"]] = relationship(
        back_populates="photo_set", cascade="all, delete-orphan"
    )


class QuotePhoto(Base):
    __tablename__ = "quote_photos"
    __table_args__ = (Index("ix_quote_photos_set_id", "set_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote_photo_sets.id", ondelete="CASCADE"), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(String(120), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    photo_set: Mapped[QuotePhotoSet] = relationship(back_populates="photos")
