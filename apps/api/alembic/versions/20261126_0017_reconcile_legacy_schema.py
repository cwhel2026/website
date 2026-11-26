"""Reconcile legacy create_all databases; auditor role; scheduler heartbeats

Revision ID: 20261126_0017
Revises: 20251126_0016

Production was built by the old startup ``create_all``, which creates missing
tables but never adds columns to existing ones and never extends enum types.
Revisions 0002-0016 (now existence-checked) add what they know about; this
revision adds whatever is still missing relative to the models as of this
revision. It is additive only: nothing is dropped, renamed or rewritten.

Enum labels are stored as member *names* (``OWNER``), so the lowercase
``'accountant'`` label added by 0008 never matched ``UserRole.ACCOUNTANT``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.registry import load_all_models
from app.schema import ops as safe
from app.schema.reconcile import reconcile

revision: str = "20261126_0017"
down_revision: str | Sequence[str] | None = "20251126_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BASELINE_FLAG = "surfacecoat_baseline_bootstrap"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.info.get(BASELINE_FLAG):
        return

    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'ACCOUNTANT'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'AUDITOR'")

    safe.create_table(
        "scheduler_heartbeats",
        sa.Column("component", sa.String(40), primary_key=True),
        sa.Column("hostname", sa.String(200), nullable=True),
        sa.Column("last_beat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=False, server_default="{}"),
    )

    reconcile(bind, load_all_models())


def downgrade() -> None:
    # Additive reconciliation is intentionally not reversed: dropping columns
    # or tables could destroy production data.
    op.drop_table("scheduler_heartbeats")
