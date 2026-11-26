"""Stage 6 Phase D — remuneration and director loan

Revision ID: 20251125_0007
Revises: 20251125_0006
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.schema import ops as safe

revision: str = "20251125_0007"
down_revision: Union[str, None] = "20251125_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE dividend_proposal_status AS ENUM "
        "('draft','awaiting_approval','approved','rejected','paid'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE directors_loan_entry_kind AS ENUM "
        "('withdrawal','introduction','repayment','adjustment'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    safe.create_table(
        "dividend_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("amount_gbp", sa.Numeric(12, 2), nullable=False),
        sa.Column("proposed_payment_date", sa.Date(), nullable=False),
        sa.Column("distributable_profit_at_proposal_gbp", sa.Numeric(12, 2), nullable=False),
        sa.Column("company_cash_at_proposal_gbp", sa.Numeric(12, 2), nullable=False),
        sa.Column("lawful", sa.Boolean(), server_default="false"),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "awaiting_approval",
                "approved",
                "rejected",
                "paid",
                name="dividend_proposal_status",
                create_type=False,
            ),
            server_default="draft",
        ),
        sa.Column("board_minutes_text", sa.Text(), nullable=True),
        sa.Column("voucher_text", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    safe.create_table(
        "directors_loan_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "kind",
            sa.Enum(
                "withdrawal",
                "introduction",
                "repayment",
                "adjustment",
                name="directors_loan_entry_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("amount_gbp", sa.Numeric(12, 2), nullable=False),
        sa.Column("transacted_at", sa.Date(), nullable=False),
        sa.Column("note", sa.String(255), nullable=False),
        sa.Column("bank_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_directors_loan_entries_kind", "directors_loan_entries", ["kind"])


def downgrade() -> None:
    op.drop_table("directors_loan_entries")
    op.drop_table("dividend_proposals")
    op.execute("DROP TYPE IF EXISTS directors_loan_entry_kind")
    op.execute("DROP TYPE IF EXISTS dividend_proposal_status")