"""Private quotation photographs and condition review.

Revision ID: 20261127_0021
Revises: 20261127_0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from app.schema import ops as safe

revision: str = "20261127_0021"
down_revision: str | None = "20261127_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    safe.create_table(
        "quote_photo_sets",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("token", sa.String(length=80), nullable=False),
        sa.Column("customer_note", sa.Text(), nullable=True),
        sa.Column("quotation_id", sa.UUID(), nullable=True),
        sa.Column("enquiry_id", sa.UUID(), nullable=True),
        sa.Column("customer_id", sa.UUID(), nullable=True),
        sa.Column("property_id", sa.UUID(), nullable=True),
        sa.Column("marketing_use_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ai_status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("findings_json", JSONB(), nullable=True),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "review_status",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'not_required'"),
        ),
        sa.Column("repair_price_gbp", sa.Numeric(12, 2), nullable=True),
        sa.Column("repair_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["enquiry_id"], ["enquiries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["property_id"], ["customer_properties.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("token", name="uq_quote_photo_sets_token"),
    )
    safe.create_index("ix_quote_photo_sets_quotation_id", "quote_photo_sets", ["quotation_id"])
    safe.create_table(
        "quote_photos",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("set_id", sa.UUID(), nullable=False),
        sa.Column("storage_key", sa.String(length=120), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["set_id"], ["quote_photo_sets.id"], ondelete="CASCADE"),
    )
    safe.create_index("ix_quote_photos_set_id", "quote_photos", ["set_id"])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS quote_photos")
    op.execute("DROP TABLE IF EXISTS quote_photo_sets")
