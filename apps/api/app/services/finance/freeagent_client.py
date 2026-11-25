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


async def api_post(
    settings: Settings, access_token: str, path: str, body: dict[str, Any]
) -> dict[str, Any]:
    base = settings.freeagent_api_base.rstrip("/")
    url = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        if not resp.content:
            return {}
        return resp.json()


async def api_put(
    settings: Settings, access_token: str, path: str, body: dict[str, Any]
) -> dict[str, Any]:
    base = settings.freeagent_api_base.rstrip("/")
    url = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.put(url, headers=headers, json=body)
        resp.raise_for_status()
        if not resp.content:
            return {}
        return resp.json()


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


async def fetch_paginated_list(
    settings: Settings,
    access_token: str,
    path: str,
    list_key: str,
    *,
    max_pages: int = 25,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in path else "?"
        payload = await api_get(settings, access_token, f"{path}{sep}page={page}&per_page=50")
        batch = payload.get(list_key) or []
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        total = payload.get("total")
        if total is not None and page * 50 >= int(total):
            break
        if len(batch) < 50:
            break
    return items


async def fetch_bills(settings: Settings, access_token: str) -> list[dict[str, Any]]:
    return await fetch_paginated_list(settings, access_token, "/v2/bills", "bills")


async def fetch_expenses(settings: Settings, access_token: str) -> list[dict[str, Any]]:
    return await fetch_paginated_list(settings, access_token, "/v2/expenses", "expenses")


async def profit_and_loss_summary(
    settings: Settings, access_token: str, *, from_date: str, to_date: str
) -> dict[str, Any]:
    path = f"/v2/accounting/profit_and_loss/summary?from_date={from_date}&to_date={to_date}"
    return await api_get(settings, access_token, path)


async def balance_sheet_summary(
    settings: Settings, access_token: str, *, as_at_date: str | None = None
) -> dict[str, Any]:
    path = "/v2/accounting/balance_sheet/summary"
    if as_at_date:
        path += f"?as_at_date={as_at_date}"
    return await api_get(settings, access_token, path)


async def trial_balance_summary(
    settings: Settings, access_token: str, *, to_date: str | None = None
) -> dict[str, Any]:
    path = "/v2/accounting/trial_balance/summary"
    if to_date:
        path += f"?to_date={to_date}"
    return await api_get(settings, access_token, path)


async def fetch_categories(settings: Settings, access_token: str) -> dict[str, Any]:
    return await api_get(settings, access_token, "/v2/categories")


async def fetch_payroll_year(settings: Settings, access_token: str, year: int) -> dict[str, Any]:
    return await api_get(settings, access_token, f"/v2/payroll/{year}")


async def fetch_payroll_period(settings: Settings, access_token: str, year: int, period: int) -> dict[str, Any]:
    return await api_get(settings, access_token, f"/v2/payroll/{year}/{period}")


async def attach_explanation_receipt(
    settings: Settings,
    access_token: str,
    explanation_path: str,
    *,
    dated_on: str,
    gross_value: str,
    bank_transaction_url: str,
    file_name: str,
    content_type: str,
    data_b64: str,
    description: str,
) -> dict[str, Any]:
    """PUT bank transaction explanation with base64 attachment — FreeAgent authoritative."""
    path = explanation_path if explanation_path.startswith("/") else f"/v2/bank_transaction_explanations/{explanation_path.rsplit('/', 1)[-1]}"
    body = {
        "bank_transaction_explanation": {
            "dated_on": dated_on,
            "gross_value": gross_value,
            "bank_transaction": bank_transaction_url,
            "attachment": {
                "file_name": file_name,
                "content_type": content_type,
                "data": data_b64,
                "description": description,
            },
        }
    }
    return await api_put(settings, access_token, path, body)


async def fetch_users_me(settings: Settings, access_token: str) -> dict[str, Any]:
    return await api_get(settings, access_token, "/v2/users/me")


async def create_expense_with_attachment(
    settings: Settings,
    access_token: str,
    *,
    user_url: str,
    category_url: str,
    dated_on: str,
    description: str,
    gross_value: str,
    sales_tax_value: str,
    file_name: str,
    content_type: str,
    data_b64: str,
) -> dict[str, Any]:
    """Director personal expense reimbursement — requires approval before call."""
    body = {
        "expense": {
            "user": user_url,
            "category": category_url,
            "dated_on": dated_on,
            "description": description[:255],
            "gross_value": gross_value,
            "sales_tax_value": sales_tax_value,
            "attachment": {
                "file_name": file_name[:200],
                "content_type": content_type,
                "data": data_b64,
            },
        }
    }
    return await api_post(settings, access_token, "/v2/expenses", body)


async def fetch_company_name(settings: Settings, access_token: str) -> str | None:
    try:
        payload = await api_get(settings, access_token, "/v2/company")
        company = payload.get("company") or {}
        return company.get("name") or company.get("url")
    except httpx.HTTPError:
        return None