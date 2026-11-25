import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DividendProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class DirectorsLoanEntryKind(str, enum.Enum):
    WITHDRAWAL = "withdrawal"
    INTRODUCTION = "introduction"
    REPAYMENT = "repayment"
    ADJUSTMENT = "adjustment"


class DividendProposal(Base):
    __tablename__ = "dividend_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    proposed_payment_date: Mapped[date] = mapped_column(Date)
    distributable_profit_at_proposal_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    company_cash_at_proposal_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    lawful: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[DividendProposalStatus] = mapped_column(
        Enum(DividendProposalStatus, name="dividend_proposal_status"), default=DividendProposalStatus.DRAFT
    )
    board_minutes_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    voucher_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DirectorsLoanEntry(Base):
    __tablename__ = "directors_loan_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[DirectorsLoanEntryKind] = mapped_column(
        Enum(DirectorsLoanEntryKind, name="directors_loan_entry_kind"), index=True
    )
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    transacted_at: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(255))
    bank_transaction_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())