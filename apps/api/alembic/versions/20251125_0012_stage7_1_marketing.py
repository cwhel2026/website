"""Stage 7.1 marketing completion

Revision ID: 20251125_0012
Revises: 20251125_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from app.schema import ops as safe

revision: str = "20251125_0012"
down_revision: str | Sequence[str] | None = "20251125_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    safe.add_column("commercial_prospects", sa.Column("google_place_id", sa.String(120), nullable=True))
    safe.add_column("commercial_prospects", sa.Column("registered_address", sa.Text(), nullable=True))
    safe.add_column("commercial_prospects", sa.Column("trading_premises_note", sa.Text(), nullable=True))
    safe.add_column("commercial_prospects", sa.Column("responsible_org_hint", sa.String(255), nullable=True))
    safe.create_index("ix_commercial_prospects_google_place_id", "commercial_prospects", ["google_place_id"], unique=True)

    safe.add_column("outreach_messages", sa.Column("sequence_step", sa.Integer(), server_default="1"))
    safe.add_column("outreach_messages", sa.Column("provider_message_id", sa.String(255), nullable=True))
    safe.add_column("outreach_messages", sa.Column("delivery_status", sa.String(40), server_default="pending"))
    safe.add_column("outreach_messages", sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True))
    safe.add_column("outreach_messages", sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True))

    safe.add_column("attribution_events", sa.Column("utm_campaign", sa.String(120), nullable=True))
    safe.add_column("attribution_events", sa.Column("utm_source", sa.String(80), nullable=True))
    safe.add_column("attribution_events", sa.Column("utm_medium", sa.String(80), nullable=True))
    safe.add_column("attribution_events", sa.Column("utm_content", sa.String(120), nullable=True))
    safe.add_column("attribution_events", sa.Column("utm_term", sa.String(120), nullable=True))

    safe.add_column("marketing_budget_policies", sa.Column("research_api_daily_limit_gbp", sa.Numeric(12, 2), server_default="5"))
    safe.add_column("marketing_budget_policies", sa.Column("outreach_email_enabled", sa.Boolean(), server_default="false"))
    safe.add_column("marketing_budget_policies", sa.Column("outreach_daily_cap", sa.Integer(), server_default="20"))

    safe.create_table(
        "marketing_email_suppressions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email_normalized", sa.String(320), unique=True, index=True),
        sa.Column("reason", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_table(
        "marketing_prospect_research_runs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("territory_id", sa.UUID(), sa.ForeignKey("territories.id"), nullable=True),
        sa.Column("category", sa.String(80)),
        sa.Column("sources_json", JSONB),
        sa.Column("imported_count", sa.Integer(), server_default="0"),
        sa.Column("api_cost_estimate_gbp", sa.Numeric(10, 4), server_default="0"),
        sa.Column("status", sa.String(40), server_default="completed"),
        sa.Column("detail_json", JSONB),
        sa.Column("ran_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_table(
        "marketing_integration_secrets",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("provider", sa.String(40), unique=True),
        sa.Column("encrypted_payload", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_table(
        "marketing_before_after_packages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_id", sa.UUID(), nullable=True),
        sa.Column("before_asset_id", sa.UUID(), sa.ForeignKey("marketing_media_assets.id"), nullable=True),
        sa.Column("after_asset_id", sa.UUID(), sa.ForeignKey("marketing_media_assets.id"), nullable=True),
        sa.Column("layout_status", sa.String(40), server_default="pending"),
        sa.Column("content_item_id", sa.UUID(), sa.ForeignKey("marketing_content_items.id"), nullable=True),
        sa.Column("customer_permission", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.add_column("marketing_media_assets", sa.Column("category", sa.String(40), server_default="general"))
    safe.add_column("marketing_media_assets", sa.Column("telegram_file_id", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("marketing_media_assets", "telegram_file_id")
    op.drop_column("marketing_media_assets", "category")
    op.drop_table("marketing_before_after_packages")
    op.drop_table("marketing_integration_secrets")
    op.drop_table("marketing_prospect_research_runs")
    op.drop_table("marketing_email_suppressions")
    op.drop_column("marketing_budget_policies", "outreach_daily_cap")
    op.drop_column("marketing_budget_policies", "outreach_email_enabled")
    op.drop_column("marketing_budget_policies", "research_api_daily_limit_gbp")
    for col in ("utm_term", "utm_content", "utm_medium", "utm_source", "utm_campaign"):
        op.drop_column("attribution_events", col)
    for col in ("replied_at", "bounced_at", "delivery_status", "provider_message_id", "sequence_step"):
        op.drop_column("outreach_messages", col)
    op.drop_index("ix_commercial_prospects_google_place_id", table_name="commercial_prospects")
    for col in ("responsible_org_hint", "trading_premises_note", "registered_address", "google_place_id"):
        op.drop_column("commercial_prospects", col)