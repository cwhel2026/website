"""SurfaceCoat Growth Fund ledger

Revision ID: 20251126_0016
Revises: 20251126_0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from app.schema import ops as safe

revision: str = "20251126_0016"
down_revision: str | Sequence[str] | None = "20251126_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE growth_fund_entry_type AS ENUM ("
        "'opening_balance','revenue_allocation','ad_expenditure','committed_budget',"
        "'refund_adjustment','manual_contribution','reversal','transfer_recommendation'"
        "); EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    safe.create_table(
        "marketing_growth_fund_settings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("allocation_pct", sa.Numeric(5, 2), server_default="5", nullable=False),
        sa.Column("initial_launch_contribution_gbp", sa.Numeric(12, 2), server_default="0"),
        sa.Column("initial_launch_recorded", sa.Boolean(), server_default="false"),
        sa.Column("mettle_pot_status", sa.String(40), server_default="virtual_reserve"),
        sa.Column("notes", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_table(
        "marketing_growth_fund_ledger",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "entry_type",
            sa.Enum(
                "opening_balance",
                "revenue_allocation",
                "ad_expenditure",
                "committed_budget",
                "refund_adjustment",
                "manual_contribution",
                "reversal",
                "transfer_recommendation",
                name="growth_fund_entry_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("amount_gbp", sa.Numeric(12, 2), nullable=False),
        sa.Column("eligible_revenue_gbp", sa.Numeric(12, 2)),
        sa.Column("allocation_pct", sa.Numeric(5, 2)),
        sa.Column("bank_transaction_id", sa.UUID(), sa.ForeignKey("bank_transactions.id"), nullable=True),
        sa.Column("invoice_id", sa.UUID(), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("campaign_id", sa.UUID(), nullable=True),
        sa.Column("dedupe_key", sa.String(120), unique=True, nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("metadata_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_growth_fund_ledger_created", "marketing_growth_fund_ledger", ["created_at"])
    safe.add_column(
        "company_profiles",
        sa.Column("marketing_revenue_allocation_pct", sa.Numeric(5, 2), server_default="5"),
    )