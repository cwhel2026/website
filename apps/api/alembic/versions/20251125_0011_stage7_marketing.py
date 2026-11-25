"""Stage 7 marketing department foundation

Revision ID: 20251125_0011
Revises: 20251125_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20251125_0011"
down_revision: str | Sequence[str] | None = "20251125_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marketing_budget_policies",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("live_paid_spend_approved", sa.Boolean(), server_default="false"),
        sa.Column("emergency_pause_all", sa.Boolean(), server_default="false"),
        sa.Column("daily_limit_gbp", sa.Numeric(12, 2), server_default="0"),
        sa.Column("weekly_limit_gbp", sa.Numeric(12, 2), server_default="0"),
        sa.Column("monthly_limit_gbp", sa.Numeric(12, 2), server_default="0"),
        sa.Column("meta_daily_limit_gbp", sa.Numeric(12, 2), server_default="0"),
        sa.Column("google_daily_limit_gbp", sa.Numeric(12, 2), server_default="0"),
        sa.Column("max_single_increase_pct", sa.Numeric(5, 2), server_default="20"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE content_platform AS ENUM "
        "('facebook','instagram','tiktok','google_business','website'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE content_status AS ENUM "
        "('draft','pending_approval','approved','scheduled','published','failed','rejected'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE outreach_message_status AS ENUM "
        "('draft','pending_approval','approved','sent','replied','suppressed','failed'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.create_table(
        "commercial_prospects",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("dedupe_key", sa.String(64), unique=True, index=True),
        sa.Column("business_name", sa.String(255), index=True),
        sa.Column("business_type", sa.String(120)),
        sa.Column("site_address", sa.Text()),
        sa.Column("postcode", sa.String(12), index=True),
        sa.Column("territory_id", sa.UUID(), sa.ForeignKey("territories.id"), nullable=True),
        sa.Column("website", sa.String(255)),
        sa.Column("contact_name", sa.String(200)),
        sa.Column("contact_email", sa.String(320)),
        sa.Column("contact_phone", sa.String(40)),
        sa.Column("source_name", sa.String(120)),
        sa.Column("source_url", sa.String(500)),
        sa.Column("verified_on", sa.Date()),
        sa.Column("confidence", sa.Integer(), server_default="50"),
        sa.Column("opportunity_category", sa.String(120)),
        sa.Column("lead_score", sa.Integer(), server_default="0"),
        sa.Column(
            "outreach_status",
            sa.Enum(name="outreach_status", create_type=False),
            server_default="new",
        ),
        sa.Column("lawful_basis", sa.String(80)),
        sa.Column("is_corporate_subscriber", sa.Boolean()),
        sa.Column("opt_out", sa.Boolean(), server_default="false"),
        sa.Column("evidence_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "outreach_messages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("prospect_id", sa.UUID(), sa.ForeignKey("commercial_prospects.id", ondelete="CASCADE")),
        sa.Column("subject", sa.String(255)),
        sa.Column("body_text", sa.Text()),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_approval",
                "approved",
                "sent",
                "replied",
                "suppressed",
                "failed",
                name="outreach_message_status",
            ),
        ),
        sa.Column("approved_by", sa.String(120)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "marketing_media_assets",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("storage_key", sa.String(255)),
        sa.Column("filename", sa.String(255)),
        sa.Column("content_sha256", sa.String(64), index=True),
        sa.Column("mime_type", sa.String(80)),
        sa.Column("job_id", sa.UUID()),
        sa.Column("source", sa.String(40)),
        sa.Column("customer_permission", sa.Boolean(), server_default="false"),
        sa.Column("is_ai_generated", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "marketing_content_items",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "platform",
            sa.Enum(
                "facebook",
                "instagram",
                "tiktok",
                "google_business",
                "website",
                name="content_platform",
            ),
        ),
        sa.Column("title", sa.String(255)),
        sa.Column("body_text", sa.Text()),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_approval",
                "approved",
                "scheduled",
                "published",
                "failed",
                "rejected",
                name="content_status",
            ),
        ),
        sa.Column("scheduled_for", sa.DateTime(timezone=True)),
        sa.Column("media_asset_ids", JSONB),
        sa.Column("publish_external_id", sa.String(120)),
        sa.Column("publish_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "territory_intelligence_scores",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("territory_id", sa.UUID(), sa.ForeignKey("territories.id"), unique=True),
        sa.Column("opportunity_score", sa.Integer(), server_default="0"),
        sa.Column("demand_indicator", sa.Integer(), server_default="0"),
        sa.Column("competition_indicator", sa.Integer(), server_default="0"),
        sa.Column("recommended_action", sa.Text()),
        sa.Column("evidence_json", JSONB),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("territory_intelligence_scores")
    op.drop_table("marketing_content_items")
    op.drop_table("marketing_media_assets")
    op.drop_table("outreach_messages")
    op.drop_table("commercial_prospects")
    op.drop_table("marketing_budget_policies")
    op.execute("DROP TYPE IF EXISTS content_platform")
    op.execute("DROP TYPE IF EXISTS content_status")
    op.execute("DROP TYPE IF EXISTS outreach_message_status")