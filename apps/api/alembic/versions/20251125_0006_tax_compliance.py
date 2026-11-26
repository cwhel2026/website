"""Stage 6 Phase C — tax reserves and compliance calendar

Revision ID: 20251125_0006
Revises: 20251125_0005
Create Date: 2025-11-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.schema import ops as safe

revision: str = "20251125_0006"
down_revision: Union[str, None] = "20251125_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE compliance_status AS ENUM "
        "('not_applicable','information_required','upcoming','preparation_required',"
        "'awaiting_approval','submitted','accepted','payment_required','completed','overdue'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    safe.create_table(
        "compliance_obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("plain_language", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("rule_version", sa.String(40), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "not_applicable",
                "information_required",
                "upcoming",
                "preparation_required",
                "awaiting_approval",
                "submitted",
                "accepted",
                "payment_required",
                "completed",
                "overdue",
                name="compliance_status",
                create_type=False,
            ),
            nullable=False,
            server_default="upcoming",
        ),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_compliance_obligations_slug", "compliance_obligations", ["slug"])
    safe.create_index("ix_compliance_obligations_due_date", "compliance_obligations", ["due_date"])

    safe.create_table(
        "tax_reserve_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("rule_version", sa.String(40), nullable=False),
        sa.Column("corporation_tax_gbp", sa.String(32), nullable=False),
        sa.Column("vat_provision_gbp", sa.String(32), nullable=False),
        sa.Column("paye_provision_gbp", sa.String(32), nullable=False),
        sa.Column("recommended_total_gbp", sa.String(32), nullable=False),
        sa.Column("assumptions_json", sa.Text(), server_default="{}"),
        sa.Column("data_freshness_note", sa.Text(), nullable=False),
        sa.Column("is_provisional", sa.Boolean(), server_default="true"),
    )
    safe.create_index("ix_tax_reserve_snapshots_computed_at", "tax_reserve_snapshots", ["computed_at"])


def downgrade() -> None:
    op.drop_table("tax_reserve_snapshots")
    op.drop_table("compliance_obligations")
    op.execute("DROP TYPE IF EXISTS compliance_status")