from unittest.mock import AsyncMock

import httpx
import pytest

from app.services.telegram import client


@pytest.mark.asyncio
async def test_timeout_does_not_expose_bot_token(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(client, "get_settings", lambda: SimpleNamespace(telegram_bot_token="secret-token"))
    post = AsyncMock(side_effect=httpx.ReadTimeout("https://api.telegram.org/botsecret-token/sendMessage"))
    context = AsyncMock()
    context.__aenter__.return_value = SimpleNamespace(post=post)
    monkeypatch.setattr(client.httpx, "AsyncClient", lambda **kwargs: context)
    with pytest.raises(client.TelegramApiError) as error:
        await client.send_message(chat_id=1, text="test")
    assert "secret-token" not in str(error.value)
    assert error.value.__suppress_context__
