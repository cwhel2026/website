"""Widen Telegram chat IDs without discarding existing messages."""
from alembic import op
import sqlalchemy as sa

revision = "20261128_0024"
down_revision = "20261128_0023"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("telegram_processed_updates", "telegram_conversation_messages"):
        op.alter_column(table, "chat_id", existing_type=sa.Integer(), type_=sa.BigInteger())


def downgrade():
    # Never silently truncate identifiers; PostgreSQL rejects out-of-range values.
    for table in ("telegram_processed_updates", "telegram_conversation_messages"):
        op.alter_column(table, "chat_id", existing_type=sa.BigInteger(), type_=sa.Integer())
