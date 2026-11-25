"""Incremental FreeAgent synchronisation with audit trail — FreeAgent remains authoritative."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.finance import BankTransaction, FreeAgentConnectionState, SyncSource
from app.models.finance_sync import FinanceSyncKind, FinanceSyncRun, FinanceSyncStatus
from app.services.finance import freeagent_client
from app.services.finance.freeagent_adapter import (
    ensure_fresh_token,
    freeagent_status,
    get_connection_row,
    sync_invoices_from_freeagent,
)


def _parse_fa_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return date.today()


async def _begin_sync_run(db: AsyncSession, kind: FinanceSyncKind, dedupe_key: str | None) -> FinanceSyncRun:
    run = FinanceSyncRun(kind=kind, status=FinanceSyncStatus.RUNNING, dedupe_key=dedupe_key)
    db.add(run)
    await db.flush()
    return run


async def sync_bank_transactions_from_freeagent(db: AsyncSession) -> dict:
    settings = get_settings()
    status = await freeagent_status(db)
    if not status.can_sync:
        return {"fetched": 0, "imported": 0, "message": status.message}

    row = await get_connection_row(db)
    if row is None:
        return {"fetched": 0, "imported": 0, "message": "Not connected"}

    dedupe_key = f"freeagent-bank:{datetime.now(UTC).date().isoformat()}"
    existing_run = await db.execute(
        select(FinanceSyncRun).where(
            FinanceSyncRun.dedupe_key == dedupe_key,
            FinanceSyncRun.status == FinanceSyncStatus.SUCCEEDED,
        )
    )
    if existing_run.scalar_one_or_none():
        return {"fetched": 0, "imported": 0, "message": "Bank sync already completed today"}

    run = await _begin_sync_run(db, FinanceSyncKind.FREEAGENT_BANK, dedupe_key)

    try:
        token = await ensure_fresh_token(db, row, settings)
        accounts = await freeagent_client.fetch_bank_accounts(settings, token)
    except (httpx.HTTPError, ValueError) as exc:
        run.status = FinanceSyncStatus.FAILED
        run.error_message = str(exc)
        run.finished_at = datetime.now(UTC)
        await db.flush()
        return {"fetched": 0, "imported": 0, "message": str(exc)}

    if not accounts:
        run.status = FinanceSyncStatus.SKIPPED
        run.detail_json = json.dumps({"reason": "no_bank_accounts"})
        run.finished_at = datetime.now(UTC)
        await db.flush()
        return {"fetched": 0, "imported": 0, "message": "No bank accounts returned from FreeAgent"}

    existing_ids = await db.execute(
        select(BankTransaction.external_id).where(BankTransaction.source == SyncSource.FREEAGENT)
    )
    known = {x for x in existing_ids.scalars().all() if x}

    fetched = 0
    imported = 0
    skipped = 0

    for account in accounts:
        account_url = account.get("url") or ""
        if not account_url:
            continue
        page = 1
        while page <= 20:
            try:
                txns, total = await freeagent_client.fetch_bank_transactions(
                    settings, token, account_url, page=page, per_page=50
                )
            except httpx.HTTPError:
                break
            fetched += len(txns)
            for item in txns:
                fa_url = str(item.get("url") or "")
                ext_id = fa_url.rsplit("/", 1)[-1] if fa_url else None
                if not ext_id or ext_id in known:
                    skipped += 1
                    continue
                amount = item.get("amount")
                description = str(item.get("description") or item.get("long_description") or "Bank line")
                try:
                    amount_dec = Decimal(str(amount))
                except Exception:
                    continue
                txn = BankTransaction(
                    external_id=ext_id,
                    description=description[:255],
                    amount_gbp=amount_dec,
                    transacted_at=_parse_fa_date(item.get("dated_on")),
                    source=SyncSource.FREEAGENT,
                )
                db.add(txn)
                known.add(ext_id)
                imported += 1
            if total is not None and page * 50 >= total:
                break
            if len(txns) < 50:
                break
            page += 1

    run.fetched_count = fetched
    run.applied_count = imported
    run.skipped_duplicates = skipped
    run.status = FinanceSyncStatus.SUCCEEDED if imported or fetched else FinanceSyncStatus.PARTIAL
    run.finished_at = datetime.now(UTC)
    run.detail_json = json.dumps({"accounts": len(accounts)})
    row.last_sync_at = datetime.now(UTC)
    await db.flush()
    return {
        "fetched": fetched,
        "imported": imported,
        "skipped_duplicates": skipped,
        "message": f"Imported {imported} new bank lines ({skipped} duplicates skipped).",
    }


async def sync_all_freeagent(db: AsyncSession) -> dict:
    invoices = await sync_invoices_from_freeagent(db)
    bank = await sync_bank_transactions_from_freeagent(db)
    return {"invoices": invoices, "bank": bank}