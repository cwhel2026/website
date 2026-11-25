"""Register Telegram webhook using server environment variables."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import urllib.error
import urllib.request

from app.config import get_settings

logger = logging.getLogger(__name__)
TELEGRAM_API = "https://api.telegram.org"


class WebhookRegistrationError(RuntimeError):
    pass


def normalise_telegram_webhook_secret(raw: str) -> str:
    trimmed = (raw or "").strip()
    if not trimmed:
        return ""
    if re.fullmatch(r"[A-Za-z0-9_-]+", trimmed):
        return trimmed
    return hashlib.sha256(trimmed.encode("utf-8")).hexdigest()


def _api_base_url() -> str:
    settings = get_settings()
    explicit = (settings.public_api_base_url or "").strip().rstrip("/")
    if explicit:
        return explicit
    import os

    railway_domain = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if railway_domain:
        return f"https://{railway_domain.rstrip('/')}"
    raise WebhookRegistrationError(
        "Set PUBLIC_API_BASE_URL (or RAILWAY_PUBLIC_DOMAIN) on the API service."
    )


def _telegram_post(token: str, method: str, body: dict) -> dict:
    url = f"{TELEGRAM_API}/bot{token}/{method}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:400]
        raise WebhookRegistrationError(f"Telegram {method} HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise WebhookRegistrationError(f"Telegram {method}: {exc.reason}") from exc
    if not payload.get("ok"):
        raise WebhookRegistrationError(payload.get("description", f"Telegram {method} failed"))
    return payload


def _telegram_get(token: str, method: str) -> dict:
    url = f"{TELEGRAM_API}/bot{token}/{method}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:400]
        raise WebhookRegistrationError(f"Telegram {method} HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise WebhookRegistrationError(f"Telegram {method}: {exc.reason}") from exc
    if not payload.get("ok"):
        raise WebhookRegistrationError(payload.get("description", f"Telegram {method} failed"))
    return payload


def public_webhook_info(info: dict) -> dict:
    result = info.get("result") or {}
    return {
        "webhook_url": result.get("url") or "",
        "pending_update_count": result.get("pending_update_count"),
        "last_error_message": result.get("last_error_message"),
        "last_error_date": result.get("last_error_date"),
        "max_connections": result.get("max_connections"),
    }


def register_telegram_webhook(*, drop_pending: bool = True) -> dict:
    settings = get_settings()
    token = (settings.telegram_bot_token or "").strip()
    secret = normalise_telegram_webhook_secret(settings.telegram_webhook_secret or "")
    if not token:
        raise WebhookRegistrationError("TELEGRAM_BOT_TOKEN not set")
    if not secret:
        raise WebhookRegistrationError("TELEGRAM_WEBHOOK_SECRET not set")

    base = _api_base_url()
    webhook_url = f"{base}/api/v1/telegram/webhook"

    body = {
        "url": webhook_url,
        "secret_token": secret,
        "drop_pending_updates": drop_pending,
        "allowed_updates": ["message"],
    }
    _telegram_post(token, "setWebhook", body)
    info = _telegram_get(token, "getWebhookInfo")
    safe = public_webhook_info(info)
    configured = (safe.get("webhook_url") or "").rstrip("/") == webhook_url.rstrip("/")
    logger.info(
        "Telegram webhook registration complete url=%s pending=%s last_error=%s ok=%s",
        safe.get("webhook_url"),
        safe.get("pending_update_count"),
        safe.get("last_error_message"),
        configured,
    )
    return {
        "registered_url": webhook_url,
        "verified_url_match": configured,
        "telegram": safe,
    }