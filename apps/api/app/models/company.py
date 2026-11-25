import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LegalStructure(str, enum.Enum):
    UK_PRIVATE_LIMITED = "uk_private_limited"


class VatStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"
    APPLIED = "applied"


class PayrollStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"


class OnboardingTaskStatus(str, enum.Enum):
    NOT_APPLICABLE = "not_applicable"
    INFO_REQUIRED = "information_required"
    UPCOMING = "upcoming"
    PREPARATION_REQUIRED = "preparation_required"
    AWAITING_APPROVAL = "awaiting_approval"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class CompanyProfile(Base):
    """Revive My Drive Ltd — single-company record (not multi-tenant)."""

    __tablename__ = "company_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    legal_structure: Mapped[LegalStructure] = mapped_column(
        Enum(LegalStructure, name="legal_structure"),
        default=LegalStructure.UK_PRIVATE_LIMITED,
    )
    registered_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    companies_house_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    incorporation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trading_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registered_office: Mapped[str | None] = mapped_column(Text, nullable=True)
    accounting_reference_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accounting_reference_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_utr: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vat_status: Mapped[VatStatus] = mapped_column(
        Enum(VatStatus, name="vat_status"), default=VatStatus.UNKNOWN
    )
    vat_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    paye_status: Mapped[PayrollStatus] = mapped_column(
        Enum(PayrollStatus, name="payroll_status"), default=PayrollStatus.UNKNOWN
    )
    paye_reference: Mapped[str | None] = mapped_column(String(32), nullable=True)
    corporation_tax_registered: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    accountant_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    accountant_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    shareholders_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    directors_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    director_desired_monthly_net_gbp: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    mettle_account_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    freeagent_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CompanyOnboardingTask(Base):
    __tablename__ = "company_onboarding_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    plain_language: Mapped[str] = mapped_column(Text)
    status: Mapped[OnboardingTaskStatus] = mapped_column(
        Enum(OnboardingTaskStatus, name="onboarding_task_status"),
        default=OnboardingTaskStatus.INFO_REQUIRED,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )