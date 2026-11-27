from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.finance import FreeAgentConnection, FreeAgentConnectionState, Invoice, InvoiceStatus
from app.services.finance import freeagent_client
from app.services.finance.token_vault import (
    decrypt_token,
    encrypt_token,
    encryption_configured,
    reencrypt_if_legacy,
)


@dataclass
class FreeAgentStatus:
    state: FreeAgentConnectionState
    message: str
    can_sync: bool
    organisation_name: str | None = None
    last_sync_at: datetime | None = None


async def get_connection_row(db: AsyncSession) -> FreeAgentConnection | None:
    result = await db.execute(select(FreeAgentConnection).limit(1))
    return result.scalar_one_or_none()


def _credentials_configured(settings: Settings) -> bool:
    return bool(
        settings.freeagent_client_id
        and settings.freeagent_client_secret
        and settings.freeagent_redirect_uri
    )


async def freeagent_status(db: AsyncSession) -> FreeAgentStatus:
    settings = get_settings()
    row = await get_connection_row(db)

    if not _credentials_configured(settings):
        return FreeAgentStatus(
            FreeAgentConnectionState.NOT_CONFIGURED,
            "Set FREEAGENT_CLIENT_ID, FREEAGENT_CLIENT_SECRET, and FREEAGENT_REDIRECT_URI.",
            False,
        )

    if row and row.state == FreeAgentConnectionState.CONNECTED and _clear_access_token(row):
        return FreeAgentStatus(
            FreeAgentConnectionState.CONNECTED,
            "Connected — invoice sync available.",
            True,
            organisation_name=row.organisation_name,
            last_sync_at=row.last_sync_at,
        )

    if row and row.state == FreeAgentConnectionState.ERROR:
        return FreeAgentStatus(
            FreeAgentConnectionState.ERROR,
            row.last_error or "Connection error — reconnect FreeAgent.",
            False,
            organisation_name=row.organisation_name,
            last_sync_at=row.last_sync_at,
        )

    return FreeAgentStatus(
        FreeAgentConnectionState.PENDING_OAUTH,
        "Credentials configured — complete OAuth from the Finance dashboard.",
        False,
        organisation_name=row.organisation_name if row else None,
    )


async def begin_oauth(db: AsyncSession) -> dict:
    settings = get_settings()
    if not _credentials_configured(settings):
        raise ValueError("FreeAgent OAuth is not configured on this deployment")
    if not encryption_configured():
        raise ValueError(
            "FINANCE_TOKEN_ENCRYPTION_KEY (32+ characters) must be set before connecting FreeAgent"
        )
    row = await get_connection_row(db)
    if row is None:
        row = FreeAgentConnection(state=FreeAgentConnectionState.PENDING_OAUTH)
        db.add(row)
    state = freeagent_client.new_oauth_state()
    row.oauth_state = state
    row.state = FreeAgentConnectionState.PENDING_OAUTH
    row.last_error = None
    await db.flush()
    url = freeagent_client.authorization_url(settings, state)
    return {"authorize_url": url, "state": state}


async def complete_oauth(db: AsyncSession, code: str, state: str) -> dict:
    settings = get_settings()
    row = await get_connection_row(db)
    if row is None or not row.oauth_state or not hmac.compare_digest(row.oauth_state, state or ""):
        raise ValueError("Invalid or expired OAuth state — start connect again")
    try:
        payload = await freeagent_client.exchange_code_for_tokens(settings, code)
    except httpx.HTTPError as exc:
        row.state = FreeAgentConnectionState.ERROR
        row.last_error = f"Token exchange failed: {exc}"
        row.oauth_state = None
        await db.flush()
        raise

    row.access_token = encrypt_token(payload.get("access_token"))
    row.refresh_token = encrypt_token(
        payload.get("refresh_token") or decrypt_token(row.refresh_token)
    )
    row.token_expires_at = freeagent_client.token_expiry_from_payload(payload)
    row.oauth_state = None
    row.state = FreeAgentConnectionState.CONNECTED
    clear_access = decrypt_token(row.access_token)
    if clear_access:
        row.organisation_name = await freeagent_client.fetch_company_name(settings, clear_access)
    from app.services.company.onboarding import get_or_create_profile

    profile = await get_or_create_profile(db)
    profile.freeagent_configured = True
    row.last_error = None
    await db.flush()
    return {"state": row.state.value, "organisation_name": row.organisation_name}


def _clear_access_token(row: FreeAgentConnection) -> str | None:
    row.access_token = reencrypt_if_legacy(row.access_token)
    return decrypt_token(row.access_token)


def _clear_refresh_token(row: FreeAgentConnection) -> str | None:
    row.refresh_token = reencrypt_if_legacy(row.refresh_token)
    return decrypt_token(row.refresh_token)


async def ensure_fresh_token(db: AsyncSession, row: FreeAgentConnection, settings: Settings) -> str:
    access = _clear_access_token(row)
    if not access:
        raise ValueError("FreeAgent not connected")
    if row.token_expires_at and row.token_expires_at > datetime.now(UTC) + timedelta(minutes=2):
        return access
    refresh = _clear_refresh_token(row)
    if not refresh:
        return access
    try:
        payload = await freeagent_client.refresh_access_token(settings, refresh)
    except httpx.HTTPError as exc:
        row.state = FreeAgentConnectionState.ERROR
        row.last_error = f"Token refresh failed: {exc}"
        await db.flush()
        raise
    row.access_token = encrypt_token(payload.get("access_token")) or row.access_token
    row.refresh_token = encrypt_token(payload.get("refresh_token") or refresh) or row.refresh_token
    row.token_expires_at = freeagent_client.token_expiry_from_payload(payload)
    await db.flush()
    access = _clear_access_token(row)
    if not access:
        raise ValueError("Token refresh produced empty access token")
    return access


def _freeagent_id_from_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/").split("/")[-1]


def apply_remote_invoice_balance(inv: Invoice, item: dict) -> bool:
    """Only apply complete, internally consistent GBP invoice snapshots."""
    try:
        if item.get("currency", "GBP") != "GBP":
            return False
        total = Decimal(str(item["total_value"]))
        net = Decimal(str(item["net_value"]))
        due = Decimal(str(item["due_value"]))
        if not all(v.is_finite() for v in (total, net, due)) or not 0 <= net <= total or not 0 <= due <= total:
            return False
        status = str(item.get("status", "")).lower()
        if status not in {"draft", "sent", "paid", "overdue", "part paid", "part_paid", "scheduled"}:
            return False
        if status == "paid" and due != 0:
            return False
        inv.total_inc_vat_gbp = total
        inv.subtotal_ex_vat_gbp = net
        inv.vat_gbp = total - net
        inv.amount_paid_gbp = total - due
        inv.status = (InvoiceStatus.DRAFT if status == "draft" else InvoiceStatus.PAID if due == 0 else InvoiceStatus.PART_PAID if due < total else InvoiceStatus.OVERDUE if status == "overdue" else InvoiceStatus.SENT)
        return True
    except (KeyError, ValueError, ArithmeticError, TypeError):
        return False


async def sync_invoices_from_freeagent(db: AsyncSession) -> dict:
    settings = get_settings()
    status = await freeagent_status(db)
    if not status.can_sync:
        return {"synced": 0, "fetched": 0, "message": status.message}

    row = await get_connection_row(db)
    if row is None or not row.access_token:
        return {"synced": 0, "fetched": 0, "message": "Not connected"}

    try:
        token = await ensure_fresh_token(db, row, settings)
        remote = await freeagent_client.fetch_invoices(settings, token)
    except (httpx.HTTPError, ValueError) as exc:
        row.state = FreeAgentConnectionState.ERROR
        row.last_error = str(exc)
        row.last_sync_at = datetime.now(UTC)
        await db.flush()
        return {"synced": 0, "fetched": 0, "message": row.last_error}

    local = await db.execute(select(Invoice).where(Invoice.freeagent_id.is_not(None)).with_for_update())
    by_fa_id = {inv.freeagent_id: inv for inv in local.scalars().all() if inv.freeagent_id}

    updated = 0
    for item in remote:
        fa_url = item.get("url")
        fa_id = _freeagent_id_from_url(fa_url)
        if not fa_id:
            continue
        inv = by_fa_id.get(fa_id)
        if inv is None:
            continue
        if not apply_remote_invoice_balance(inv, item):
            continue
        inv.freeagent_url = fa_url
        updated += 1

    row.last_sync_at = datetime.now(UTC)
    row.last_error = None
    await db.flush()
    return {
        "synced": updated,
        "fetched": len(remote),
        "message": f"Matched {updated} of {len(remote)} FreeAgent invoices to local records.",
    }