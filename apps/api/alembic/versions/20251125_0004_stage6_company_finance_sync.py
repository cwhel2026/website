"""Stage 6 Phase A — company profile, onboarding tasks, finance sync audit

Revision ID: 20251125_0004
Revises: 20251125_0003
Create Date: 2025-11-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.schema import ops as safe

revision: str = "20251125_0004"
down_revision: Union[str, None] = "20251125_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE legal_structure AS ENUM ('uk_private_limited'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE vat_status AS ENUM "
        "('unknown','not_registered','registered','applied'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE payroll_status AS ENUM "
        "('unknown','not_registered','registered'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE onboarding_task_status AS ENUM "
        "('not_applicable','information_required','upcoming','preparation_required',"
        "'awaiting_approval','submitted','completed','overdue'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE finance_sync_kind AS ENUM "
        "('freeagent_invoices','freeagent_bank','freeagent_contacts','freeagent_bills','freeagent_full'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE finance_sync_status AS ENUM "
        "('running','succeeded','partial','failed','skipped'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    safe.create_table(
        "company_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "legal_structure",
            sa.Enum("uk_private_limited", name="legal_structure", create_type=False),
            nullable=False,
            server_default="uk_private_limited",
        ),
        sa.Column("registered_name", sa.String(200), nullable=True),
        sa.Column("companies_house_number", sa.String(16), nullable=True),
        sa.Column("incorporation_date", sa.Date(), nullable=True),
        sa.Column("trading_start_date", sa.Date(), nullable=True),
        sa.Column("registered_office", sa.Text(), nullable=True),
        sa.Column("accounting_reference_month", sa.Integer(), nullable=True),
        sa.Column("accounting_reference_day", sa.Integer(), nullable=True),
        sa.Column("company_utr", sa.String(20), nullable=True),
        sa.Column(
            "vat_status",
            sa.Enum(
                "unknown",
                "not_registered",
                "registered",
                "applied",
                name="vat_status",
                create_type=False,
            ),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("vat_number", sa.String(20), nullable=True),
        sa.Column(
            "paye_status",
            sa.Enum("unknown", "not_registered", "registered", name="payroll_status", create_type=False),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("paye_reference", sa.String(32), nullable=True),
        sa.Column("corporation_tax_registered", sa.Boolean(), nullable=True),
        sa.Column("accountant_name", sa.String(200), nullable=True),
        sa.Column("accountant_email", sa.String(320), nullable=True),
        sa.Column("shareholders_json", postgresql.JSONB(), nullable=True),
        sa.Column("directors_json", postgresql.JSONB(), nullable=True),
        sa.Column("mettle_account_hint", sa.String(255), nullable=True),
        sa.Column("freeagent_configured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    safe.create_table(
        "company_onboarding_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("plain_language", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "not_applicable",
                "information_required",
                "upcoming",
                "preparation_required",
                "awaiting_approval",
                "submitted",
                "completed",
                "overdue",
                name="onboarding_task_status",
                create_type=False,
            ),
            nullable=False,
            server_default="information_required",
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_company_onboarding_tasks_slug", "company_onboarding_tasks", ["slug"])

    safe.create_table(
        "finance_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "kind",
            sa.Enum(
                "freeagent_invoices",
                "freeagent_bank",
                "freeagent_contacts",
                "freeagent_bills",
                "freeagent_full",
                name="finance_sync_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "running",
                "succeeded",
                "partial",
                "failed",
                "skipped",
                name="finance_sync_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(120), nullable=True),
        sa.Column(
            "freeagent_connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("freeagent_connections.id"),
            nullable=True,
        ),
    )
    safe.create_index("ix_finance_sync_runs_kind", "finance_sync_runs", ["kind"])
    safe.create_index("ix_finance_sync_runs_status", "finance_sync_runs", ["status"])
    safe.create_index("ix_finance_sync_runs_dedupe_key", "finance_sync_runs", ["dedupe_key"])


def downgrade() -> None:
    op.drop_table("finance_sync_runs")
    op.drop_table("company_onboarding_tasks")
    op.drop_table("company_profiles")
    op.execute("DROP TYPE IF EXISTS finance_sync_status")
    op.execute("DROP TYPE IF EXISTS finance_sync_kind")
    op.execute("DROP TYPE IF EXISTS onboarding_task_status")
    op.execute("DROP TYPE IF EXISTS payroll_status")
    op.execute("DROP TYPE IF EXISTS vat_status")
    op.execute("DROP TYPE IF EXISTS legal_structure")