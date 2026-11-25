"""Read-only Telegram bot webhook status (no secrets in return values)."""

from __future__ import annotations

import httpx

from app.config import get_settings

TELEGRAM_API = "https://api.telegram.org"


async def fetch_webhook_info() -> dict:
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        return {"configured": False, "reason": "TELEGRAM_BOT_TOKEN not set"}
    url = f"{TELEGRAM_API}/bot{token}/getWebhookInfo"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url)
        data = response.json()
    if not data.get("ok"):
        return {
            "configured": False,
            "reason": data.get("description", "getWebhookInfo failed"),
        }
    info = data.get("result") or {}
    return {
        "configured": True,
        "webhook_url": info.get("url") or "",
        "has_custom_certificate": info.get("has_custom_certificate"),
        "pending_update_count": info.get("pending_update_count"),
        "last_error_message": info.get("last_error_message"),
        "last_error_date": info.get("last_error_date"),
        "max_connections": info.get("max_connections"),
    }