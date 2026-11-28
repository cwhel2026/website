"""Separate specialist conversation histories."""
from alembic import op
import sqlalchemy as sa

revision = "20261128_0025"
down_revision = "20261128_0024"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    table = "telegram_conversation_messages"
    if "agent_slug" not in {c["name"] for c in inspector.get_columns(table)}:
        op.add_column(table, sa.Column("agent_slug", sa.String(60), server_default="personal_assistant", nullable=False))
    if "ix_telegram_conversation_messages_agent_slug" not in {i["name"] for i in inspector.get_indexes(table)}:
        op.create_index("ix_telegram_conversation_messages_agent_slug", table, ["agent_slug"])


def downgrade():
    op.drop_index("ix_telegram_conversation_messages_agent_slug", table_name="telegram_conversation_messages")
    op.drop_column("telegram_conversation_messages", "agent_slug")
