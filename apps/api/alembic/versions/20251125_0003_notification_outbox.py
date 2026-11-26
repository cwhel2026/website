"""Notification outbox and Telegram conversation tables

Revision ID: 20251125_0003
Revises: 20251124_0002
Create Date: 2025-11-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.schema import ops as safe

revision: str = "20251125_0003"
down_revision: Union[str, None] = "20251124_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

notification_priority = sa.Enum(
    "low", "normal", "high", "urgent", name="notification_priority", create_type=False
)
outbox_status = sa.Enum(
    "pending",
    "sending",
    "delivered",
    "failed",
    "cancelled",
    name="outbox_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE notification_priority AS ENUM "
        "('low','normal','high','urgent'); EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE outbox_status AS ENUM "
        "('pending','sending','delivered','failed','cancelled'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    safe.create_table(
        "notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dedupe_key", sa.String(160), nullable=True),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("priority", notification_priority, nullable=False, server_default="normal"),
        sa.Column("category", sa.String(80), nullable=False, server_default="general"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", outbox_status, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_notification_outbox_dedupe_key", "notification_outbox", ["dedupe_key"])
    safe.create_index("ix_notification_outbox_channel", "notification_outbox", ["channel"])
    safe.create_index("ix_notification_outbox_category", "notification_outbox", ["category"])
    safe.create_index("ix_notification_outbox_status", "notification_outbox", ["status"])

    safe.create_table(
        "telegram_processed_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("update_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("update_id", name="uq_telegram_update_id"),
    )
    safe.create_index("ix_telegram_processed_updates_update_id", "telegram_processed_updates", ["update_id"])

    safe.create_table(
        "telegram_conversation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(12), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("telegram_message_id", sa.Integer(), nullable=True),
        sa.Column("outbox_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notification_outbox.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    safe.create_index("ix_telegram_conversation_messages_chat_id", "telegram_conversation_messages", ["chat_id"])


def downgrade() -> None:
    op.drop_table("telegram_conversation_messages")
    op.drop_table("telegram_processed_updates")
    op.drop_table("notification_outbox")
    op.execute("DROP TYPE IF EXISTS outbox_status")
    op.execute("DROP TYPE IF EXISTS notification_priority")