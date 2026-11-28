"""Persist encrypted Google Workspace connection."""
from alembic import op
import sqlalchemy as sa

revision = "20261128_0027"
down_revision = "20261128_0025"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("oauth_state_hash", sa.String(64), nullable=True),
        sa.Column("oauth_verifier", sa.Text(), nullable=True),
        sa.Column("oauth_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table("workspace_connections")
