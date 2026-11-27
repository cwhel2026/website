"""Customer conversion fields on enquiries.

Revision ID: 20261127_0020
Revises: 20261127_0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.schema import ops as safe

revision: str = "20261127_0020"
down_revision: str | None = "20261127_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    safe.add_column("enquiries", sa.Column("quotation_id", sa.UUID(), nullable=True))
    safe.add_column("enquiries", sa.Column("intention", sa.String(length=40), nullable=True))
    safe.add_column(
        "enquiries",
        sa.Column("priority", sa.String(length=20), nullable=False, server_default=sa.text("'normal'")),
    )
    safe.add_column("enquiries", sa.Column("callback_phone", sa.String(length=40), nullable=True))
    safe.add_column("enquiries", sa.Column("callback_preferred_time", sa.String(length=160), nullable=True))
    safe.add_column(
        "enquiries",
        sa.Column("callback_status", sa.String(length=40), nullable=False, server_default=sa.text("'not_applicable'")),
    )
    safe.add_column("enquiries", sa.Column("callback_outcome", sa.Text(), nullable=True))
    safe.add_column(
        "enquiries",
        sa.Column("email_delivery", sa.String(length=40), nullable=False, server_default=sa.text("'not_requested'")),
    )
    safe.add_column(
        "enquiries",
        sa.Column("telegram_notified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    safe.create_index("ix_enquiries_quotation_id", "enquiries", ["quotation_id"])


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_enquiries_quotation_id")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS telegram_notified")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS email_delivery")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS callback_outcome")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS callback_status")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS callback_preferred_time")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS callback_phone")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS priority")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS intention")
    op.execute("ALTER TABLE enquiries DROP COLUMN IF EXISTS quotation_id")
