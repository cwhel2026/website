"""Stage 6 Phase B — bookkeeping review queue and receipt fields

Revision ID: 20251125_0005
Revises: 20251125_0004
Create Date: 2025-11-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.schema import ops as safe

revision: str = "20251125_0005"
down_revision: Union[str, None] = "20251125_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE bookkeeping_review_status AS ENUM "
        "('pending','auto_applied','approved','rejected','escalated'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    safe.add_column("receipts", sa.Column("content_sha256", sa.String(64), nullable=True))
    safe.add_column("receipts", sa.Column("telegram_file_id", sa.String(128), nullable=True))
    safe.add_column("receipts", sa.Column("extracted_net_gbp", sa.Numeric(12, 2), nullable=True))
    safe.add_column("receipts", sa.Column("extracted_vat_gbp", sa.Numeric(12, 2), nullable=True))
    safe.add_column("receipts", sa.Column("extracted_vat_number", sa.String(32), nullable=True))
    safe.add_column("receipts", sa.Column("extracted_date", sa.Date(), nullable=True))
    safe.add_column("receipts", sa.Column("payment_method", sa.String(80), nullable=True))
    safe.add_column(
        "receipts",
        sa.Column("matched_bank_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    safe.add_column("receipts", sa.Column("processing_status", sa.String(40), server_default="pending"))
    safe.add_column("receipts", sa.Column("raw_extraction_json", sa.Text(), nullable=True))
    safe.create_index("ix_receipts_content_sha256", "receipts", ["content_sha256"])

    safe.add_column(
        "bank_transactions",
        sa.Column(
            "suggested_category",
            sa.Enum(
                "materials",
                "fuel",
                "advertising",
                "equipment",
                "insurance",
                "professional",
                "other",
                name="expense_category",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    safe.add_column("bank_transactions", sa.Column("categorisation_confidence", sa.Integer(), nullable=True))
    safe.add_column("bank_transactions", sa.Column("review_item_id", postgresql.UUID(as_uuid=True), nullable=True))
    safe.add_column(
        "bank_transactions",
        sa.Column("is_reconciled", sa.Boolean(), server_default="false", nullable=False),
    )

    safe.create_table(
        "bookkeeping_review_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "bank_transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bank_transactions.id"),
            nullable=True,
        ),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("receipts.id"),
            nullable=True,
        ),
        sa.Column(
            "suggested_category",
            sa.Enum(
                "materials",
                "fuel",
                "advertising",
                "equipment",
                "insurance",
                "professional",
                "other",
                name="expense_category",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("confidence_score", sa.Integer(), server_default="0"),
        sa.Column("plain_explanation", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "auto_applied",
                "approved",
                "rejected",
                "escalated",
                name="bookkeeping_review_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("is_personal_expenditure", sa.Boolean(), server_default="false"),
        sa.Column("receipt_required", sa.Boolean(), server_default="false"),
        sa.Column("vat_likely", sa.Boolean(), server_default="false"),
        sa.Column("possible_duplicate", sa.Boolean(), server_default="false"),
        sa.Column("matched_invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("context_json", postgresql.JSONB(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index(
        "ix_bookkeeping_review_items_bank_transaction_id",
        "bookkeeping_review_items",
        ["bank_transaction_id"],
    )
    safe.create_index(
        "ix_bookkeeping_review_items_receipt_id", "bookkeeping_review_items", ["receipt_id"]
    )


def downgrade() -> None:
    op.drop_table("bookkeeping_review_items")
    op.drop_column("bank_transactions", "is_reconciled")
    op.drop_column("bank_transactions", "review_item_id")
    op.drop_column("bank_transactions", "categorisation_confidence")
    op.drop_column("bank_transactions", "suggested_category")
    op.drop_index("ix_receipts_content_sha256", table_name="receipts")
    op.drop_column("receipts", "raw_extraction_json")
    op.drop_column("receipts", "processing_status")
    op.drop_column("receipts", "matched_bank_transaction_id")
    op.drop_column("receipts", "payment_method")
    op.drop_column("receipts", "extracted_date")
    op.drop_column("receipts", "extracted_vat_number")
    op.drop_column("receipts", "extracted_vat_gbp")
    op.drop_column("receipts", "extracted_net_gbp")
    op.drop_column("receipts", "telegram_file_id")
    op.drop_column("receipts", "content_sha256")
    op.execute("DROP TYPE IF EXISTS bookkeeping_review_status")