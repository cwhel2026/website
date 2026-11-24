"""Initial Phase 1 schema

Revision ID: 20251124_0001
Revises:
Create Date: 2025-11-24
"""

from typing import Sequence, Union

revision: str = "20251124_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema is created via SQLAlchemy metadata on API startup in development.
    # Generate a full revision with `alembic revision --autogenerate` once PostGIS is available.
    pass


def downgrade() -> None:
    pass