"""Telegram outbox stays recoverable when credentials or delivery fail."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.models.notifications import OutboxStatus
from app.services.notifications.outbox import deliver_telegram_outbox_item


class _Item:
    id = "outbox-1"
    category = "general"
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
    db = SimpleNamespace(add=lambda *_a, **_k: None, flush=AsyncMock(), refresh=AsyncMock())
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


@pytest.mark.asyncio
async def test_partial_delivery_retries_only_failed_recipient(monkeypatch):
    import json
    from app.services.notifications import outbox as mod
    from app.services.telegram.client import TelegramApiError

    item = _Item()
    db = SimpleNamespace(add=lambda *_: None, flush=AsyncMock(), refresh=AsyncMock())
    monkeypatch.setattr(mod, "get_settings", lambda: SimpleNamespace(telegram_bot_token="test", telegram_alert_chat_ids=[1, 2]))
    send = AsyncMock(side_effect=[{"message_id": 1}, TelegramApiError("failure"), {"message_id": 2}])
    monkeypatch.setattr(mod, "send_message", send)
    assert not await mod.deliver_telegram_outbox_item(db, item)
    assert item.status == OutboxStatus.PENDING
    assert json.loads(item.payload_json)["telegram_chat_ids"] == [1]
    assert await mod.deliver_telegram_outbox_item(db, item)
    assert item.status == OutboxStatus.DELIVERED
    assert [call.kwargs["chat_id"] for call in send.await_args_list] == [1, 2, 2]


@pytest.mark.asyncio
async def test_private_reply_delivery_and_revocation(monkeypatch):
    from app.services.notifications import outbox as mod
    from app.services.telegram.client import TelegramApiError

    item = _Item()
    item.category = "assistant_reply"
    item.title = ""
    item.payload_json = '{"reply_chat_id": 1}'
    db = SimpleNamespace(add=lambda *_: None, flush=AsyncMock(), refresh=AsyncMock())
    cfg = SimpleNamespace(telegram_bot_token="test", telegram_alert_chat_ids=[1, 2], telegram_admin_id_list=[1, 2])
    monkeypatch.setattr(mod, "get_settings", lambda: cfg)
    send = AsyncMock(side_effect=[TelegramApiError("failure"), {"message_id": 3}])
    monkeypatch.setattr(mod, "send_message", send)
    assert not await mod.deliver_telegram_outbox_item(db, item)
    assert await mod.deliver_telegram_outbox_item(db, item)
    assert [call.kwargs["chat_id"] for call in send.await_args_list] == [1, 1]
    revoked = _Item()
    revoked.category = "assistant_reply"
    revoked.payload_json = '{"reply_chat_id": 1}'
    cfg.telegram_admin_id_list = [2]
    assert not await mod.deliver_telegram_outbox_item(db, revoked)
    assert revoked.status == OutboxStatus.CANCELLED
    assert send.await_count == 2
