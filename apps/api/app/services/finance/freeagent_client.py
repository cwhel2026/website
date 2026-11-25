"""FreeAgent OAuth2 + REST helpers (verify against your sandbox before prod sync)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import Settings


def authorization_url(settings: Settings, state: str) -> str:
    if not settings.freeagent_client_id or not settings.freeagent_redirect_uri:
        raise ValueError("FREEAGENT_CLIENT_ID and FREEAGENT_REDIRECT_URI required")
    params = {
        "client_id": settings.freeagent_client_id,
        "response_type": "code",
        "redirect_uri": settings.freeagent_redirect_uri,
        "state": state,
    }
    base = settings.freeagent_api_base.rstrip("/")
    return f"{base}/v2/approve_app?{urlencode(params)}"


def new_oauth_state() -> str:
    return secrets.token_urlsafe(24)


async def exchange_code_for_tokens(
    settings: Settings, code: str
) -> dict[str, Any]:
    base = settings.freeagent_api_base.rstrip("/")
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.freeagent_redirect_uri,
        "client_id": settings.freeagent_client_id,
        "client_secret": settings.freeagent_client_secret,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{base}/v2/token_endpoint", data=data)
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(settings: Settings, refresh_token: str) -> dict[str, Any]:
    base = settings.freeagent_api_base.rstrip("/")
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.freeagent_client_id,
        "client_secret": settings.freeagent_client_secret,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{base}/v2/token_endpoint", data=data)
        resp.raise_for_status()
        return resp.json()


def token_expiry_from_payload(payload: dict[str, Any]) -> datetime | None:
    expires_in = payload.get("expires_in")
    if expires_in is None:
        return None
    try:
        return datetime.now(UTC) + timedelta(seconds=int(expires_in))
    except (TypeError, ValueError):
        return None


async def api_get(settings: Settings, access_token: str, path: str) -> dict[str, Any]:
    base = settings.freeagent_api_base.rstrip("/")
    url = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def fetch_invoices(settings: Settings, access_token: str) -> list[dict[str, Any]]:
    payload = await api_get(settings, access_token, "/v2/invoices")
    invoices = payload.get("invoices") or []
    if not isinstance(invoices, list):
        return []
    return invoices


async def fetch_bank_accounts(settings: Settings, access_token: str) -> list[dict[str, Any]]:
    payload = await api_get(settings, access_token, "/v2/bank_accounts")
    accounts = payload.get("bank_accounts") or []
    return accounts if isinstance(accounts, list) else []


async def fetch_bank_transactions(
    settings: Settings,
    access_token: str,
    bank_account_path: str,
    *,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[dict[str, Any]], int | None]:
    """bank_account_path is the URL suffix from FreeAgent, e.g. /v2/bank_accounts/123."""
    path = f"{bank_account_path}/bank_transactions?page={page}&per_page={per_page}"
    payload = await api_get(settings, access_token, path)
    txns = payload.get("bank_transactions") or []
    if not isinstance(txns, list):
        txns = []
    total = payload.get("total")
    try:
        total_i = int(total) if total is not None else None
    except (TypeError, ValueError):
        total_i = None
    return txns, total_i


async def fetch_company_name(settings: Settings, access_token: str) -> str | None:
    try:
        payload = await api_get(settings, access_token, "/v2/company")
        company = payload.get("company") or {}
        return company.get("name") or company.get("url")
    except httpx.HTTPError:
        return None