"""Persistent notification outbox with Telegram delivery."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.notifications import NotificationOutbox, NotificationPriority, OutboxStatus
from app.services.telegram.client import TelegramApiError, send_message

logger = logging.getLogger(__name__)


async def enqueue_notification(
    db: AsyncSession,
    *,
    channel: str,
    title: str,
    body: str,
    category: str = "general",
    priority: NotificationPriority = NotificationPriority.NORMAL,
    dedupe_key: str | None = None,
    payload: dict | None = None,
    scheduled_for: datetime | None = None,
    max_attempts: int = 5,
) -> NotificationOutbox:
    if dedupe_key:
        existing = await db.execute(
            select(NotificationOutbox).where(
                NotificationOutbox.dedupe_key == dedupe_key,
                NotificationOutbox.status.in_(
                    [OutboxStatus.PENDING, OutboxStatus.SENDING, OutboxStatus.DELIVERED]
                ),
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            return row

    item = NotificationOutbox(
        channel=channel,
        title=title,
        body=body,
        category=category,
        priority=priority,
        dedupe_key=dedupe_key,
        payload_json=json.dumps(payload or {}),
        scheduled_for=scheduled_for,
        max_attempts=max_attempts,
    )
    db.add(item)
    await db.flush()
    return item


async def deliver_telegram_outbox_item(db: AsyncSession, item: NotificationOutbox) -> bool:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_admin_id_list:
        item.last_error = "Telegram not configured"
        item.status = OutboxStatus.FAILED
        db.add(item)
        return False

    chat_id = settings.telegram_admin_id_list[0]
    item.status = OutboxStatus.SENDING
    item.attempts += 1
    db.add(item)
    await db.flush()

    text = f"{item.title}\n\n{item.body}" if item.title else item.body
    try:
        result = await send_message(chat_id=chat_id, text=text)
        item.status = OutboxStatus.DELIVERED
        item.delivered_at = datetime.now(UTC)
        item.last_error = None
        payload = json.loads(item.payload_json or "{}")
        payload["telegram_message_id"] = result.get("message_id")
        item.payload_json = json.dumps(payload)
        db.add(item)
        return True
    except TelegramApiError as exc:
        logger.warning("Telegram delivery failed for outbox %s: %s", item.id, exc)
        item.last_error = str(exc)
        if item.attempts >= item.max_attempts:
            item.status = OutboxStatus.FAILED
        else:
            item.status = OutboxStatus.PENDING
        db.add(item)
        return False


async def process_pending_telegram(db: AsyncSession, *, limit: int = 20) -> int:
    now = datetime.now(UTC)
    result = await db.execute(
        select(NotificationOutbox)
        .where(
            NotificationOutbox.channel == "telegram",
            NotificationOutbox.status == OutboxStatus.PENDING,
            (NotificationOutbox.scheduled_for.is_(None) | (NotificationOutbox.scheduled_for <= now)),
        )
        .order_by(NotificationOutbox.created_at)
        .limit(limit)
    )
    rows = list(result.scalars().all())
    delivered = 0
    for row in rows:
        if await deliver_telegram_outbox_item(db, row):
            delivered += 1
    await db.commit()
    return delivered


async def notify_owner_telegram(
    db: AsyncSession,
    *,
    title: str,
    body: str,
    category: str,
    dedupe_key: str | None = None,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    deliver_immediately: bool = True,
) -> NotificationOutbox:
    item = await enqueue_notification(
        db,
        channel="telegram",
        title=title,
        body=body,
        category=category,
        priority=priority,
        dedupe_key=dedupe_key,
    )
    await db.commit()
    if deliver_immediately:
        await deliver_telegram_outbox_item(db, item)
        await db.commit()
    return item