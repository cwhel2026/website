#!/usr/bin/env python3
"""
Register and verify the Telegram webhook against the production FastAPI service.

Reads secrets from the environment only — never prints tokens or webhook secrets.

Required env:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_WEBHOOK_SECRET
  PUBLIC_API_BASE_URL  — scheme + host, no path (e.g. https://api-xxx.up.railway.app)

Optional env:
  RAILWAY_PUBLIC_DOMAIN — used if PUBLIC_API_BASE_URL is unset (https://<domain>)

Usage (on Railway API service or with vars exported locally):
  cd apps/api && python scripts/register_telegram_webhook.py
  python scripts/register_telegram_webhook.py --info-only
  python scripts/register_telegram_webhook.py --delete
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


def _mask(value: str | None, visible: int = 4) -> str:
    if not value:
        return "(unset)"
    if len(value) <= visible * 2:
        return "***"
    return f"{value[:visible]}…{value[-visible:]}"


def _api_base_url() -> str:
    explicit = (os.environ.get("PUBLIC_API_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    railway_domain = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if railway_domain:
        return f"https://{railway_domain.rstrip('/')}"
    raise SystemExit(
        "Set PUBLIC_API_BASE_URL to your FastAPI public origin "
        "(e.g. https://your-api-service.up.railway.app), or set RAILWAY_PUBLIC_DOMAIN on the API service."
    )


def _webhook_path() -> str:
    return "/api/v1/telegram/webhook"


def _bot_token() -> str:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set.")
    if not re.match(r"^\d+:[A-Za-z0-9_-]+$", token):
        raise SystemExit("TELEGRAM_BOT_TOKEN format looks invalid (refusing to call Telegram).")
    return token


def _webhook_secret() -> str:
    secret = (os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise SystemExit("TELEGRAM_WEBHOOK_SECRET is not set.")
    if len(secret) < 16:
        raise SystemExit("TELEGRAM_WEBHOOK_SECRET should be at least 16 characters.")
    return secret


def _telegram_post(token: str, method: str, body: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
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
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram {method} HTTP {exc.code}: {err_body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Telegram {method} network error: {exc.reason}") from exc

    if not payload.get("ok"):
        desc = payload.get("description", "unknown error")
        raise SystemExit(f"Telegram {method} failed: {desc}")
    return payload


def _telegram_get(token: str, method: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram {method} HTTP {exc.code}: {err_body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Telegram {method} network error: {exc.reason}") from exc

    if not payload.get("ok"):
        desc = payload.get("description", "unknown error")
        raise SystemExit(f"Telegram {method} failed: {desc}")
    return payload


def _check_api_health(base: str) -> None:
    health_url = f"{base}/health"
    req = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                print(f"warning: {health_url} returned HTTP {resp.status}")
            else:
                print(f"ok: API health reachable at {health_url}")
    except urllib.error.URLError as exc:
        print(f"warning: could not reach API health ({health_url}): {exc.reason}")


def _print_webhook_info(result: dict) -> None:
    info = result.get("result") or {}
    url = info.get("url") or ""
    print("--- getWebhookInfo (safe fields) ---")
    print(f"url: {url or '(none)'}")
    print(f"has_custom_certificate: {info.get('has_custom_certificate')}")
    print(f"pending_update_count: {info.get('pending_update_count')}")
    print(f"max_connections: {info.get('max_connections')}")
    if info.get("last_error_date"):
        print(f"last_error_date: {info.get('last_error_date')}")
    if info.get("last_error_message"):
        print(f"last_error_message: {info.get('last_error_message')}")
    if info.get("ip_address"):
        print(f"ip_address: {info.get('ip_address')}")
    secret_ok = "set" if info.get("url") else "unknown"
    print(f"secret_token: {secret_ok} (Telegram does not echo secret_token; must match TELEGRAM_WEBHOOK_SECRET on API)")


def register_webhook(*, dry_run: bool) -> str:
    token = _bot_token()
    secret = _webhook_secret()
    base = _api_base_url()
    webhook_url = f"{base}{_webhook_path()}"

    print(f"bot token: {_mask(token)}")
    print(f"webhook secret: {_mask(secret)}")
    print(f"webhook URL: {webhook_url}")

    _check_api_health(base)

    if dry_run:
        print("dry-run: skipping setWebhook")
        return webhook_url

    me = _telegram_get(token, "getMe")
    username = (me.get("result") or {}).get("username", "?")
    print(f"bot: @{username}")

    body = {
        "url": webhook_url,
        "secret_token": secret,
        "drop_pending_updates": True,
        "allowed_updates": ["message"],
    }
    _telegram_post(token, "setWebhook", body)
    print("setWebhook: ok")

    info = _telegram_get(token, "getWebhookInfo")
    _print_webhook_info(info)

    configured = (info.get("result") or {}).get("url") == webhook_url
    if not configured:
        raise SystemExit("getWebhookInfo URL does not match the URL we registered.")
    print("verification: webhook URL matches PUBLIC_API_BASE_URL + /api/v1/telegram/webhook")
    return webhook_url


def delete_webhook(dry_run: bool) -> None:
    token = _bot_token()
    print(f"bot token: {_mask(token)}")
    if dry_run:
        print("dry-run: skipping deleteWebhook")
        return
    _telegram_post(token, "deleteWebhook", {"drop_pending_updates": True})
    print("deleteWebhook: ok")
    info = _telegram_get(token, "getWebhookInfo")
    _print_webhook_info(info)


def main() -> None:
    parser = argparse.ArgumentParser(description="Register Telegram webhook for Revive My Drive API")
    parser.add_argument("--info-only", action="store_true", help="Only call getWebhookInfo")
    parser.add_argument("--delete", action="store_true", help="Remove webhook (deleteWebhook)")
    parser.add_argument("--dry-run", action="store_true", help="Print planned URL without calling setWebhook")
    args = parser.parse_args()

    if args.delete:
        delete_webhook(args.dry_run)
        return

    if args.info_only:
        token = _bot_token()
        print(f"bot token: {_mask(token)}")
        info = _telegram_get(token, "getWebhookInfo")
        _print_webhook_info(info)
        return

    register_webhook(dry_run=args.dry_run)
    print()
    print("Manual check: message your bot in Telegram from an account listed in TELEGRAM_ADMIN_IDS.")
    print("You should receive a real reply (not only an HTTP JSON body).")
    print("Queued notifications: ensure the Celery worker is running with TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_IDS.")


if __name__ == "__main__":
    main()