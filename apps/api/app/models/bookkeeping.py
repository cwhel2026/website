"""Intelligent bookkeeping review queue — does not mutate FreeAgent without approval."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.finance import ExpenseCategory


class ReceiptStatus(str, enum.Enum):
    PENDING_UPLOAD = "pending_upload"
    STORED = "stored"
    EXTRACTED = "extracted"
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    ATTACHED = "attached"
    FAILED = "failed"


class ReviewItemStatus(str, enum.Enum):
    PENDING = "pending"
    AUTO_APPLIED = "auto_applied"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class BookkeepingReviewItem(Base):
    __tablename__ = "bookkeeping_review_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bank_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=True, index=True
    )
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=True, index=True
    )
    suggested_category: Mapped[ExpenseCategory | None] = mapped_column(
        Enum(ExpenseCategory, name="expense_category", create_constraint=False), nullable=True
    )
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    plain_explanation: Mapped[str] = mapped_column(Text)
    status: Mapped[ReviewItemStatus] = mapped_column(
        Enum(ReviewItemStatus, name="bookkeeping_review_status"), default=ReviewItemStatus.PENDING
    )
    is_personal_expenditure: Mapped[bool] = mapped_column(Boolean, default=False)
    receipt_required: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_likely: Mapped[bool] = mapped_column(Boolean, default=False)
    possible_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    context_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

