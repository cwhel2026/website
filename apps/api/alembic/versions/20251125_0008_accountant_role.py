"""Add accountant user role enum value

Revision ID: 20251125_0008
Revises: 20251125_0007
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20251125_0008"
down_revision: Union[str, None] = "20251125_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'accountant'")


def downgrade() -> None:
    pass