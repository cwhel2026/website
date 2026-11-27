from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.notifications import OutboxStatus
from app.services.notifications import outbox
from app.routers import notifications
from app.services import quote_photo_store


@pytest.mark.asyncio
async def test_outbox_insert_is_inside_savepoint():
    events = []

    @asynccontextmanager
    async def nested():
        events.append("begin")
        yield
        events.append("end")

    async def flush():
        events.append("flush")

    db = SimpleNamespace(begin_nested=nested, add=lambda item: events.append("add"), flush=flush)
    await outbox.enqueue_notification(db, channel="telegram", title="test", body="test")
    assert events == ["begin", "add", "flush", "end"]


@pytest.mark.asyncio
async def test_retry_does_not_resend_delivered(monkeypatch):
    item = SimpleNamespace(id=uuid4(), channel="telegram", status=OutboxStatus.DELIVERED, last_error=None)
    db = SimpleNamespace(get=AsyncMock(return_value=item), commit=AsyncMock())
    send = AsyncMock()
    monkeypatch.setattr(notifications, "deliver_telegram_outbox_item", send)
    result = await notifications.retry_outbox(item.id, db, None)
    assert result["delivered"] is True
    send.assert_not_awaited()
    db.get.assert_awaited_once_with(notifications.NotificationOutbox, item.id, with_for_update=True)


def test_photo_write_is_private_and_repeatable(tmp_path, monkeypatch):
    monkeypatch.setattr(quote_photo_store, "photos_root", lambda: tmp_path)
    key, digest = quote_photo_store.save_photo_bytes(b"test payload")
    assert quote_photo_store.save_photo_bytes(b"test payload") == (key, digest)
    assert quote_photo_store.read_photo_bytes(key) == b"test payload"
    assert (tmp_path / key).stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.rglob(".photo-*"))


def test_oversize_dimensions_rejected_before_decode(monkeypatch):
    image = SimpleNamespace(width=10000, height=10000, load=lambda: pytest.fail("decoded oversized image"))
    monkeypatch.setattr(quote_photo_store.Image, "open", lambda _: image)
    with pytest.raises(ValueError):
        quote_photo_store.prepare_image(b"\\xff\\xd8\\xff".decode("unicode_escape").encode("latin1"))
