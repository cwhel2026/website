import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComplianceStatus(str, enum.Enum):
    NOT_APPLICABLE = "not_applicable"
    INFO_REQUIRED = "information_required"
    UPCOMING = "upcoming"
    PREPARATION_REQUIRED = "preparation_required"
    AWAITING_APPROVAL = "awaiting_approval"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PAYMENT_REQUIRED = "payment_required"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class ComplianceObligation(Base):
    __tablename__ = "compliance_obligations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(200))
    plain_language: Mapped[str] = mapped_column(Text)
    why_it_matters: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus, name="compliance_status"), default=ComplianceStatus.UPCOMING
    )
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaxReserveSnapshot(Base):
    __tablename__ = "tax_reserve_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    rule_version: Mapped[str] = mapped_column(String(40))
    corporation_tax_gbp: Mapped[str] = mapped_column(String(32))
    vat_provision_gbp: Mapped[str] = mapped_column(String(32))
    paye_provision_gbp: Mapped[str] = mapped_column(String(32))
    recommended_total_gbp: Mapped[str] = mapped_column(String(32))
    assumptions_json: Mapped[str] = mapped_column(Text, default="{}")
    data_freshness_note: Mapped[str] = mapped_column(Text)
    is_provisional: Mapped[bool] = mapped_column(default=True)