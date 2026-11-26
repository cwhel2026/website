"""Stage 7.3 marketing final

Revision ID: 20251126_0014
Revises: 20251126_0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from app.schema import ops as safe

revision: str = "20251126_0014"
down_revision: str | Sequence[str] | None = "20251126_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE commercial_pipeline_stage AS ENUM ("
        "'discovered','research_required','qualified','contact_verified','outreach_drafted','approved',"
        "'contacted','replied','site_survey_requested','quotation_submitted','negotiation','won','lost','do_not_contact'"
        "); EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    safe.add_column("marketing_brand_profiles", sa.Column("service_areas_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("fonts_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("tone_of_voice", sa.Text()))
    safe.add_column("marketing_brand_profiles", sa.Column("approved_claims_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("approved_ctas_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("objectives_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("differentiators_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("demographics_json", JSONB))
    safe.add_column("marketing_brand_profiles", sa.Column("photo_permission_policy", sa.Text()))
    safe.add_column(
        "commercial_prospects",
        sa.Column(
            "pipeline_stage",
            sa.Enum(name="commercial_pipeline_stage", create_type=False),
            server_default="discovered",
        ),
    )
    safe.add_column("commercial_prospects", sa.Column("contact_history_json", JSONB))
    safe.add_column("marketing_budget_policies", sa.Column("official_launch_date", sa.Date()))
    safe.create_table(
        "competitor_intelligence_findings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("competitor_name", sa.String(255), index=True),
        sa.Column("territory_code", sa.String(10)),
        sa.Column("category", sa.String(80)),
        sa.Column("finding_type", sa.String(80)),
        sa.Column("summary", sa.Text()),
        sa.Column("source_name", sa.String(120)),
        sa.Column("source_url", sa.String(500)),
        sa.Column("confidence", sa.Integer(), server_default="50"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("payload_json", JSONB),
    )
    safe.create_table(
        "marketing_launch_plans",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("launch_date", sa.Date(), nullable=True),
        sa.Column("plan_json", JSONB),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_table(
        "marketing_meta_leads",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("leadgen_id", sa.String(120), unique=True),
        sa.Column("enquiry_id", sa.UUID(), nullable=True),
        sa.Column("payload_json", JSONB),
        sa.Column("dedupe_key", sa.String(64), unique=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_table(
        "marketing_job_media_staging",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_id", sa.UUID(), nullable=True),
        sa.Column("job_reference", sa.String(24), index=True),
        sa.Column("asset_id", sa.UUID(), sa.ForeignKey("marketing_media_assets.id")),
        sa.Column("phase", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("marketing_job_media_staging")
    op.drop_table("marketing_meta_leads")
    op.drop_table("marketing_launch_plans")
    op.drop_table("competitor_intelligence_findings")
    op.drop_column("marketing_budget_policies", "official_launch_date")
    op.drop_column("commercial_prospects", "contact_history_json")
    op.drop_column("commercial_prospects", "pipeline_stage")
    for col in (
        "photo_permission_policy",
        "demographics_json",
        "differentiators_json",
        "objectives_json",
        "approved_ctas_json",
        "approved_claims_json",
        "tone_of_voice",
        "fonts_json",
        "service_areas_json",
    ):
        op.drop_column("marketing_brand_profiles", col)
    op.execute("DROP TYPE IF EXISTS commercial_pipeline_stage")