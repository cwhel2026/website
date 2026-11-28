"""Separate specialist conversation histories."""
from alembic import op
import sqlalchemy as sa

revision = "20261128_0025"
down_revision = "20261128_0024"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("telegram_conversation_messages", sa.Column("agent_slug", sa.String(60), nullable=False, server_default="personal_assistant"))
    op.create_index("ix_telegram_conversation_messages_agent_slug", "telegram_conversation_messages", ["agent_slug"])


def downgrade():
    op.drop_index("ix_telegram_conversation_messages_agent_slug", table_name="telegram_conversation_messages")
    op.drop_column("telegram_conversation_messages", "agent_slug")
