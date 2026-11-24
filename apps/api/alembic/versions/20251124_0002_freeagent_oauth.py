"""FreeAgent OAuth token columns

Revision ID: 20251124_0002
Revises: 20251124_0001
Create Date: 2025-11-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20251124_0002"
down_revision: Union[str, None] = "20251124_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE freeagent_connections ADD COLUMN IF NOT EXISTS access_token TEXT")
    op.execute("ALTER TABLE freeagent_connections ADD COLUMN IF NOT EXISTS refresh_token TEXT")
    op.execute(
        "ALTER TABLE freeagent_connections ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMPTZ"
    )
    op.execute("ALTER TABLE freeagent_connections ADD COLUMN IF NOT EXISTS oauth_state VARCHAR(64)")
    op.execute(
        "ALTER TABLE freeagent_connections ADD COLUMN IF NOT EXISTS freeagent_company_url VARCHAR(255)"
    )


def downgrade() -> None:
    op.drop_column("freeagent_connections", "freeagent_company_url")
    op.drop_column("freeagent_connections", "oauth_state")
    op.drop_column("freeagent_connections", "token_expires_at")
    op.drop_column("freeagent_connections", "refresh_token")
    op.drop_column("freeagent_connections", "access_token")