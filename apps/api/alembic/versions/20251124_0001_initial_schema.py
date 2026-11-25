"""Initial Phase 1 schema baseline

Revision ID: 20251124_0001
Revises:
Create Date: 2025-11-24

Existing Railway databases were bootstrapped via app seeds before Alembic.
This revision is a no-op when core tables already exist; it only stamps history
so later migrations (0002+) can apply safely without re-running create_all.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20251124_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CORE_TABLES = ("users", "territories", "customers")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    if any(t in existing for t in _CORE_TABLES):
        return
    # Empty database: revision recorded; run API bootstrap seeds then `alembic upgrade head`.
    return


def downgrade() -> None:
    pass