"""Telegram outbox stays recoverable when credentials or delivery fail."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.models.notifications import OutboxStatus
from app.services.notifications.outbox import deliver_telegram_outbox_item


class _Item:
    id = "outbox-1"
    status = OutboxStatus.PENDING
    last_error = None
    attempts = 0
    max_attempts = 8
    title = "TEST NOTIFICATION — SurfaceCoat"
    body = "labelled test"
    payload_json = "{}"
    delivered_at = None
    dedupe_key = "quote-conversion:1:ready_to_book"


@pytest.mark.asyncio
async def test_missing_credentials_leave_the_row_pending():
    item = _Item()
    db = SimpleNamespace(add=lambda *_a, **_k: None, flush=AsyncMock())
    from app.services.notifications import outbox as outbox_mod

    original = outbox_mod.get_settings
    outbox_mod.get_settings = lambda: SimpleNamespace(telegram_bot_token=None, telegram_alert_chat_ids=[])
    try:
        ok = await deliver_telegram_outbox_item(db, item)
    finally:
        outbox_mod.get_settings = original

    assert ok is False
    assert item.status == OutboxStatus.PENDING
    assert "not configured" in (item.last_error or "").lower()


def test_admin_ids_include_group_chats():
    settings = Settings(telegram_admin_ids="-1001234567890, 12345, not-a-chat")
    assert settings.telegram_admin_id_list == [-1001234567890, 12345]
    settings.telegram_owner_chat_id = 999
    assert settings.telegram_alert_chat_ids[0] == 999
    assert -1001234567890 in settings.telegram_alert_chat_ids
