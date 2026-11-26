"""Stage 6.2 — director pay target, receipt accounting metadata

Revision ID: 20251125_0010
Revises: 20251125_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.schema import ops as safe

revision: str = "20251125_0010"
down_revision: str | Sequence[str] | None = "20251125_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    safe.add_column(
        "company_profiles",
        sa.Column("director_desired_monthly_net_gbp", sa.Numeric(12, 2), nullable=True),
    )
    safe.add_column(
        "receipts",
        sa.Column("freeagent_expense_url", sa.String(255), nullable=True),
    )
    safe.add_column(
        "receipts",
        sa.Column("accounting_route", sa.String(40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("receipts", "accounting_route")
    op.drop_column("receipts", "freeagent_expense_url")
    op.drop_column("company_profiles", "director_desired_monthly_net_gbp")