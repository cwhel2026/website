"""Persistent notification outbox with Telegram delivery."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    max_attempts: int = 8,
) -> NotificationOutbox:
    if dedupe_key:
        existing = await db.execute(
            select(NotificationOutbox).where(NotificationOutbox.dedupe_key == dedupe_key)
        )
        row = existing.scalar_one_or_none()
        if row:
            if row.status in {OutboxStatus.FAILED, OutboxStatus.CANCELLED}:
                row.status = OutboxStatus.PENDING
                row.last_error = None
                db.add(row)
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
        status=OutboxStatus.PENDING,
    )
    try:
        async with db.begin_nested():
            db.add(item)
            await db.flush()
        return item
    except IntegrityError:
        existing = (
            await db.execute(select(NotificationOutbox).where(NotificationOutbox.dedupe_key == dedupe_key))
            if dedupe_key
            else None
        )
        row = existing.scalar_one_or_none() if existing is not None else None
        if row:
            return row
        raise


def _chat_ids() -> list[int]:
    return get_settings().telegram_alert_chat_ids


def telegram_recipients(category: str, payload: dict, settings) -> list[int]:
    if category == "assistant_reply":
        target = payload.get("reply_chat_id")
        return [target] if type(target) is int and target in settings.telegram_admin_id_list else []
    return list(dict.fromkeys(settings.telegram_alert_chat_ids))


async def deliver_telegram_outbox_item(db: AsyncSession, item: NotificationOutbox) -> bool:
    # Refresh under a row lock: immediate sends and background workers share this gate.
    await db.refresh(item, with_for_update=True)
    if item.status == OutboxStatus.DELIVERED:
        return True
    if item.status == OutboxStatus.CANCELLED:
        return False
    settings = get_settings()
    payload = json.loads(item.payload_json or "{}")
    chats = telegram_recipients(item.category, payload, settings)
    if item.category == "assistant_reply" and not chats:
        item.status = OutboxStatus.CANCELLED
        item.last_error = "Private reply recipient no longer authorised"
        await db.flush()
        return False
    if not settings.telegram_bot_token or not chats:
        item.last_error = "Telegram not configured (TELEGRAM_BOT_TOKEN or admin/owner chat id missing)"
        item.status = OutboxStatus.PENDING
        db.add(item)
        await db.flush()
        return False

    item.status = OutboxStatus.SENDING
    item.attempts += 1
    db.add(item)
    await db.flush()

    text = f"{item.title}\n\n{item.body}" if item.title else item.body
    errors: list[str] = []
    last_result: dict | None = None
    delivered_chats = list(payload.get("telegram_chat_ids", []))
    for chat_id in chats:
        if chat_id in delivered_chats:
            continue
        try:
            last_result = await send_message(chat_id=chat_id, text=text)
            delivered_chats.append(chat_id)
        except TelegramApiError as exc:
            errors.append(f"{chat_id}: Telegram delivery failed (status={exc.status_code})")

    payload["telegram_chat_ids"] = delivered_chats
    if last_result:
        payload["telegram_message_id"] = last_result.get("message_id")
    item.payload_json = json.dumps(payload)
    if all(chat_id in delivered_chats for chat_id in chats):
        item.status = OutboxStatus.DELIVERED
        item.delivered_at = datetime.now(UTC)
        item.last_error = None
        db.add(item)
        if item.dedupe_key and item.dedupe_key.startswith("fin-report:"):
            from app.services.finance.financial_reports import mark_finance_report_delivered

            await mark_finance_report_delivered(db, item.dedupe_key)
        return True

    logger.warning("Telegram delivery failed for outbox %s: %s", item.id, "; ".join(errors))
    item.last_error = "; ".join(errors)[:2000] or "Telegram sendMessage failed"
    if item.attempts >= item.max_attempts:
        item.status = OutboxStatus.FAILED
    else:
        item.status = OutboxStatus.PENDING
    db.add(item)
    await db.flush()
    return False


async def process_pending_telegram(db: AsyncSession, *, limit: int = 20) -> int:
    now = datetime.now(UTC)
    result = await db.execute(
        select(NotificationOutbox)
        .where(
            NotificationOutbox.channel == "telegram",
            NotificationOutbox.status.in_([OutboxStatus.PENDING, OutboxStatus.SENDING]),
            (NotificationOutbox.scheduled_for.is_(None) | (NotificationOutbox.scheduled_for <= now)),
        )
        .order_by(NotificationOutbox.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = list(result.scalars().all())
    delivered = 0
    for row in rows:
        if row.status == OutboxStatus.SENDING and row.attempts > 0:
            # A crashed send left the row locked in SENDING — retry it.
            row.status = OutboxStatus.PENDING
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
    payload: dict | None = None,
) -> NotificationOutbox:
    item = await enqueue_notification(
        db,
        channel="telegram",
        title=title,
        body=body,
        category=category,
        priority=priority,
        dedupe_key=dedupe_key,
        payload=payload,
    )
    await db.commit()
    if deliver_immediately:
        await deliver_telegram_outbox_item(db, item)
        await db.commit()
    return item
