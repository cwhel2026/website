"""Minimal Telegram Bot API client for outbound owner notifications."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
TELEGRAM_API = "https://api.telegram.org"


class TelegramApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


async def send_message(
    *,
    chat_id: int,
    text: str,
    parse_mode: str | None = None,
    reply_markup: dict[str, Any] | None = None,
    disable_notification: bool = False,
) -> dict[str, Any]:
    settings = get_settings()
    token = (settings.telegram_bot_token or "").strip()
    if not token:
        raise TelegramApiError("TELEGRAM_BOT_TOKEN is not configured")

    if any(ch.isspace() or ord(ch) < 32 for ch in token):
        raise TelegramApiError("Telegram bot token contains invalid whitespace")

    body: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text[:4096],
        "disable_notification": disable_notification,
    }
    if parse_mode:
        body["parse_mode"] = parse_mode
    if reply_markup:
        body["reply_markup"] = reply_markup

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=body)
            data = response.json()
        except (httpx.RequestError, httpx.InvalidURL, ValueError):
            raise TelegramApiError("Telegram transport or response failure") from None
        if not isinstance(data, dict):
            raise TelegramApiError("Invalid Telegram response")
        if response.status_code >= 400 or not data.get("ok"):
            raise TelegramApiError(
                "Telegram sendMessage rejected",
                status_code=response.status_code,
                payload=data,
            )
        return data.get("result") or {}