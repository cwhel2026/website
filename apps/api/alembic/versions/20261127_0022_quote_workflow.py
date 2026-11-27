"""Booking follow-ups, test flags, and recoverable Telegram outbox.

Revision ID: 20261127_0022
Revises: 20261127_0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.schema import ops as safe

revision: str = "20261127_0022"
down_revision: str | None = "20261127_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEST_REFERENCE = "SC-20261127-D48B"


def upgrade() -> None:
    safe.add_column("customers", sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.false()))
    safe.add_column("enquiries", sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.false()))
    safe.add_column(
        "enquiries",
        sa.Column("telegram_outbox_id", sa.UUID(), nullable=True),
    )
    safe.add_column("quotations", sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.false()))
    safe.add_column(
        "scheduling_settings",
        sa.Column("min_notice_hours", sa.Integer(), nullable=False, server_default=sa.text("24")),
    )
    safe.add_column(
        "scheduling_settings",
        sa.Column("earliest_work_date", sa.Date(), nullable=True),
    )
    op.execute("UPDATE scheduling_settings SET earliest_work_date = DATE '2027-03-01' WHERE earliest_work_date IS NULL")

    safe.create_table(
        "owner_follow_ups",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("enquiry_id", sa.UUID(), nullable=False),
        sa.Column("quotation_id", sa.UUID(), nullable=True),
        sa.Column("customer_id", sa.UUID(), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'open'")),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["enquiry_id"], ["enquiries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("enquiry_id", "kind", name="uq_owner_follow_ups_enquiry_kind"),
    )
    safe.create_index("ix_owner_follow_ups_status", "owner_follow_ups", ["status"])

    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_notification_outbox_dedupe_key
            ON notification_outbox (dedupe_key)
            WHERE dedupe_key IS NOT NULL
            """
        )
    )
    op.execute("DROP INDEX IF EXISTS ix_notification_outbox_dedupe_key")

    op.execute(
        sa.text(
            """
            UPDATE quotations q
            SET is_test = true
            WHERE q.reference = :ref
            """
        ).bindparams(ref=TEST_REFERENCE)
    )
    op.execute(
        sa.text(
            """
            UPDATE enquiries e
            SET is_test = true
            FROM quotations q
            WHERE q.enquiry_id = e.id AND q.reference = :ref
            """
        ).bindparams(ref=TEST_REFERENCE)
    )
    op.execute(
        sa.text(
            """
            UPDATE customers c
            SET is_test = true
            FROM quotations q
            WHERE q.customer_id = c.id AND q.reference = :ref
            """
        ).bindparams(ref=TEST_REFERENCE)
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_notification_outbox_dedupe_key")
    op.drop_table("owner_follow_ups")
