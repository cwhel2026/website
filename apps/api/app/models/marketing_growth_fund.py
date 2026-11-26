"""SurfaceCoat Growth Fund — virtual marketing reserve from customer revenue."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GrowthFundEntryType(str, enum.Enum):
    OPENING_BALANCE = "opening_balance"
    REVENUE_ALLOCATION = "revenue_allocation"
    AD_EXPENDITURE = "ad_expenditure"
    COMMITTED_BUDGET = "committed_budget"
    REFUND_ADJUSTMENT = "refund_adjustment"
    MANUAL_CONTRIBUTION = "manual_contribution"
    REVERSAL = "reversal"
    TRANSFER_RECOMMENDATION = "transfer_recommendation"


class MarketingGrowthFundSettings(Base):
    __tablename__ = "marketing_growth_fund_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=True)
    allocation_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5"))
    initial_launch_contribution_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    initial_launch_recorded: Mapped[bool] = mapped_column(default=False)
    mettle_pot_status: Mapped[str] = mapped_column(String(40), default="virtual_reserve")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MarketingGrowthFundLedger(Base):
    __tablename__ = "marketing_growth_fund_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_type: Mapped[GrowthFundEntryType] = mapped_column(
        Enum(GrowthFundEntryType, name="growth_fund_entry_type", create_constraint=False)
    )
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    eligible_revenue_gbp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    allocation_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    bank_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=True
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())