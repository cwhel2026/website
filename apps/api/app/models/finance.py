import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PART_PAID = "part_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class ExpenseCategory(str, enum.Enum):
    MATERIALS = "materials"
    FUEL = "fuel"
    ADVERTISING = "advertising"
    EQUIPMENT = "equipment"
    INSURANCE = "insurance"
    PROFESSIONAL = "professional"
    OTHER = "other"


class SyncSource(str, enum.Enum):
    MANUAL = "manual"
    CSV = "csv"
    FREEAGENT = "freeagent"


class FreeAgentConnectionState(str, enum.Enum):
    NOT_CONFIGURED = "not_configured"
    PENDING_OAUTH = "pending_oauth"
    CONNECTED = "connected"
    ERROR = "error"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id")
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True
    )
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id"), nullable=True
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"), default=InvoiceStatus.DRAFT
    )
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    subtotal_ex_vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_inc_vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_paid_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    freeagent_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    freeagent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1"))
    unit_price_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    line_total_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True
    )
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    method: Mapped[str] = mapped_column(String(40), default="bank_transfer")
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[SyncSource] = mapped_column(
        Enum(SyncSource, name="sync_source"), default=SyncSource.MANUAL
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    description: Mapped[str] = mapped_column(String(255))
    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory, name="expense_category"))
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vat_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    expense_date: Mapped[date] = mapped_column(Date)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    territory_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source: Mapped[SyncSource] = mapped_column(
        Enum(SyncSource, name="sync_source"), default=SyncSource.MANUAL
    )
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    telegram_file_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extracted_merchant: Mapped[str | None] = mapped_column(String(200), nullable=True)
    extracted_total_gbp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    extracted_net_gbp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    extracted_vat_gbp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    extracted_vat_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extracted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    matched_bank_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=True
    )
    processing_status: Mapped[str] = mapped_column(String(40), default="pending")
    ocr_status: Mapped[str] = mapped_column(String(40), default="not_processed")
    raw_extraction_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    freeagent_attach_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    freeagent_attach_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    freeagent_expense_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accounting_route: Mapped[str | None] = mapped_column(String(40), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BankTransaction(Base):
    """Local reporting layer — FreeAgent authoritative when connected."""

    __tablename__ = "bank_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    freeagent_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    freeagent_explanation_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(String(255))
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    transacted_at: Mapped[date] = mapped_column(Date)
    source: Mapped[SyncSource] = mapped_column(
        Enum(SyncSource, name="sync_source"), default=SyncSource.MANUAL
    )
    matched_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    matched_expense_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    suggested_category: Mapped[ExpenseCategory | None] = mapped_column(
        Enum(ExpenseCategory, name="expense_category", create_constraint=False), nullable=True
    )
    categorisation_confidence: Mapped[int | None] = mapped_column(nullable=True)
    review_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(default=False)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FreeAgentConnection(Base):
    __tablename__ = "freeagent_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    state: Mapped[FreeAgentConnectionState] = mapped_column(
        Enum(FreeAgentConnectionState, name="freeagent_state"),
        default=FreeAgentConnectionState.NOT_CONFIGURED,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    organisation_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    oauth_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    freeagent_company_url: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TaxYearSettings(Base):
    __tablename__ = "tax_year_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tax_year_label: Mapped[str] = mapped_column(String(12), default="2025-26")
    personal_allowance_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("12570"))
    basic_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("20"))
    vat_registration_threshold_gbp: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("90000")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)