"""Stage 7.2 pre-launch marketing

Revision ID: 20251126_0013
Revises: 20251125_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20251126_0013"
down_revision: str | Sequence[str] | None = "20251125_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marketing_brand_profiles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("business_name", sa.String(200), server_default="Revive My Drive Ltd"),
        sa.Column("primary_colour", sa.String(20), server_default="#047857"),
        sa.Column("secondary_colour", sa.String(20), server_default="#0f172a"),
        sa.Column("phone", sa.String(40)),
        sa.Column("website", sa.String(255), server_default="https://revivemydrive.co.uk"),
        sa.Column("tagline", sa.String(255)),
        sa.Column("logo_storage_key", sa.String(255)),
        sa.Column("services_summary", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "marketing_director_runs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("run_type", sa.String(40)),
        sa.Column("summary", sa.Text()),
        sa.Column("recommendations_json", JSONB),
        sa.Column("evidence_json", JSONB),
        sa.Column("pre_launch_mode", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "marketing_publication_log",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("content_item_id", sa.UUID(), sa.ForeignKey("marketing_content_items.id")),
        sa.Column("platform", sa.String(40)),
        sa.Column("idempotency_key", sa.String(64), unique=True),
        sa.Column("status", sa.String(40)),
        sa.Column("external_id", sa.String(120)),
        sa.Column("error", sa.Text()),
        sa.Column("simulated", sa.Boolean(), server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "marketing_rendered_creatives",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("package_id", sa.UUID(), sa.ForeignKey("marketing_before_after_packages.id")),
        sa.Column("format", sa.String(40)),
        sa.Column("storage_key", sa.String(255)),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column("commercial_prospects", sa.Column("follow_up_at", sa.DateTime(timezone=True)))
    op.add_column("commercial_prospects", sa.Column("priority_score", sa.Integer(), server_default="0"))
    op.add_column("commercial_prospects", sa.Column("estimated_value_gbp", sa.Numeric(12, 2)))
    op.add_column("commercial_prospects", sa.Column("distance_km", sa.Numeric(8, 2)))
    op.add_column("commercial_prospects", sa.Column("decision_contact_hint", sa.String(200)))
    op.add_column("commercial_prospects", sa.Column("next_action", sa.String(120)))
    op.add_column("marketing_experiments", sa.Column("min_sample_size", sa.Integer(), server_default="30"))
    op.add_column("marketing_experiments", sa.Column("metric_name", sa.String(80), server_default="quotations"))
    op.add_column("marketing_experiments", sa.Column("conclusion", sa.Text()))
    op.add_column("marketing_experiments", sa.Column("winner_variant", sa.String(1)))
    op.add_column("marketing_content_items", sa.Column("format_variant", sa.String(40)))
    op.add_column("marketing_content_items", sa.Column("idempotency_key", sa.String(64), unique=True))