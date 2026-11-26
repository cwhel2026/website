"""SurfaceCoat Meta marketing — organic posts, director mode, launch programme

Revision ID: 20251126_0015
Revises: 20251126_0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from app.schema import ops as safe

revision: str = "20251126_0015"
down_revision: str | Sequence[str] | None = "20251126_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE organic_platform AS ENUM ('facebook','instagram'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE marketing_director_mode AS ENUM "
        "('observation','recommend','controlled_auto'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    safe.create_table(
        "marketing_organic_posts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "platform",
            sa.Enum("facebook", "instagram", name="organic_platform", create_type=False),
            nullable=False,
        ),
        sa.Column("external_post_id", sa.String(120), nullable=False),
        sa.Column("permalink", sa.String(500)),
        sa.Column("caption", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("media_refs_json", JSONB),
        sa.Column("format", sa.String(40)),
        sa.Column("metrics_json", JSONB),
        sa.Column("ai_analysis_json", JSONB),
        sa.Column("raw_payload_json", JSONB),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("platform", "external_post_id", name="uq_organic_post_platform_ext"),
    )
    safe.create_index("ix_organic_posts_published", "marketing_organic_posts", ["published_at"])
    safe.create_table(
        "marketing_organic_post_snapshots",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "post_id",
            sa.UUID(),
            sa.ForeignKey("marketing_organic_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metrics_json", JSONB, nullable=False),
    )
    safe.add_column(
        "marketing_budget_policies",
        sa.Column(
            "director_operating_mode",
            sa.Enum("observation", "recommend", "controlled_auto", name="marketing_director_mode", create_type=False),
            server_default="recommend",
        ),
    )
    safe.add_column(
        "marketing_budget_policies",
        sa.Column("meta_weekly_budget_gbp", sa.Numeric(12, 2), server_default="150"),
    )
    safe.add_column(
        "marketing_budget_policies",
        sa.Column("meta_safety_buffer_pct", sa.Numeric(5, 2), server_default="5"),
    )
    safe.add_column("marketing_budget_policies", sa.Column("geo_target_json", JSONB))
    safe.add_column("marketing_budget_policies", sa.Column("launch_programme_json", JSONB))
    safe.add_column("marketing_budget_policies", sa.Column("meta_account_spend_last_gbp", sa.Numeric(12, 2)))
    safe.add_column("marketing_budget_policies", sa.Column("meta_account_spend_synced_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("marketing_budget_policies", "meta_account_spend_synced_at")
    op.drop_column("marketing_budget_policies", "meta_account_spend_last_gbp")
    op.drop_column("marketing_budget_policies", "launch_programme_json")
    op.drop_column("marketing_budget_policies", "geo_target_json")
    op.drop_column("marketing_budget_policies", "meta_safety_buffer_pct")
    op.drop_column("marketing_budget_policies", "meta_weekly_budget_gbp")
    op.drop_column("marketing_budget_policies", "director_operating_mode")
    op.drop_table("marketing_organic_post_snapshots")
    op.drop_table("marketing_organic_posts")