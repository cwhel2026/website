"""Stage 6.1 — FreeAgent cache, financial reports, bank FA urls

Revision ID: 20251125_0009
Revises: 20251125_0008
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.schema import ops as safe

revision: str = "20251125_0009"
down_revision: Union[str, None] = "20251125_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    safe.create_table(
        "freeagent_resource_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_key", sa.String(120), unique=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_freeagent_resource_cache_resource_key", "freeagent_resource_cache", ["resource_key"])

    safe.create_table(
        "financial_report_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("period", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("dashboard_path", sa.String(120), server_default="/dashboard/finance-hub"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("telegram_sent", sa.Boolean(), server_default="false"),
    )
    safe.create_index("ix_financial_report_records_period", "financial_report_records", ["period"])

    safe.add_column("bank_transactions", sa.Column("freeagent_url", sa.String(255), nullable=True))
    safe.add_column("bank_transactions", sa.Column("freeagent_explanation_url", sa.String(255), nullable=True))
    safe.add_column("receipts", sa.Column("freeagent_attach_status", sa.String(40), nullable=True))
    safe.add_column("receipts", sa.Column("freeagent_attach_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("receipts", "freeagent_attach_error")
    op.drop_column("receipts", "freeagent_attach_status")
    op.drop_column("bank_transactions", "freeagent_explanation_url")
    op.drop_column("bank_transactions", "freeagent_url")
    op.drop_table("financial_report_records")
    op.drop_table("freeagent_resource_cache")