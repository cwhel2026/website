import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QuotationSubmissionIdempotency(Base):
    """Maps client idempotency keys to persisted quotations."""

    __tablename__ = "quotation_submission_idempotency"

    idempotency_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )