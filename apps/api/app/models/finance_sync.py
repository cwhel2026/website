import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FinanceSyncKind(str, enum.Enum):
    FREEAGENT_INVOICES = "freeagent_invoices"
    FREEAGENT_BANK = "freeagent_bank"
    FREEAGENT_CONTACTS = "freeagent_contacts"
    FREEAGENT_BILLS = "freeagent_bills"
    FREEAGENT_FULL = "freeagent_full"


class FinanceSyncStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class FinanceSyncRun(Base):
    __tablename__ = "finance_sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[FinanceSyncKind] = mapped_column(
        Enum(FinanceSyncKind, name="finance_sync_kind"), index=True
    )
    status: Mapped[FinanceSyncStatus] = mapped_column(
        Enum(FinanceSyncStatus, name="finance_sync_status"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    applied_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    freeagent_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freeagent_connections.id"), nullable=True
    )