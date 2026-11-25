import json
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.freeagent_cache import FreeAgentResourceCache
from app.models.finance import Invoice, InvoiceStatus
from app.services.finance.freeagent_adapter import ensure_fresh_token, freeagent_status, get_connection_row
from app.services.finance import freeagent_client


def _extract_retained_profit(pl: dict) -> Decimal | None:
    summary = pl.get("profit_and_loss_summary") or pl.get("profit_and_loss") or pl
    for key in ("retained_profit_carried_forward", "retained-profit-carried-forward", "retained_profit"):
        val = summary.get(key)
        if val is not None:
            try:
                return Decimal(str(val))
            except Exception:
                continue
    return None


async def sync_accounting_reports(db: AsyncSession) -> dict:
    settings = get_settings()
    status = await freeagent_status(db)
    if not status.can_sync:
        return {"ok": False, "message": status.message}

    row = await get_connection_row(db)
    if row is None:
        return {"ok": False, "message": "Not connected"}

    token = await ensure_fresh_token(db, row, settings)
    today = date.today()
    from_d = today.replace(month=1, day=1) if today.month > 1 else today
    to_d = today

    results: dict = {"ok": True, "errors": []}
    try:
        pl = await freeagent_client.profit_and_loss_summary(
            settings, token, from_date=from_d.isoformat(), to_date=to_d.isoformat()
        )
        await _cache(db, "pl_summary_ytd", pl)
        retained = _extract_retained_profit(pl)
        results["retained_profit_carried_forward_gbp"] = float(retained) if retained is not None else None
    except Exception as exc:
        results["errors"].append(f"P&L: {exc}")

    try:
        bs = await freeagent_client.balance_sheet_summary(settings, token, as_at_date=today.isoformat())
        await _cache(db, "balance_sheet_latest", bs)
    except Exception as exc:
        results["errors"].append(f"Balance sheet: {exc}")

    try:
        tb = await freeagent_client.trial_balance_summary(settings, token, to_date=today.isoformat())
        await _cache(db, "trial_balance_latest", tb)
    except Exception as exc:
        results["errors"].append(f"Trial balance: {exc}")

    from datetime import UTC, datetime

    row.last_sync_at = datetime.now(UTC)
    await db.flush()
    return results


async def _cache(db: AsyncSession, key: str, payload: dict) -> None:
    text = json.dumps(payload, default=str)[:500000]
    existing = await db.execute(
        select(FreeAgentResourceCache).where(FreeAgentResourceCache.resource_key == key)
    )
    row = existing.scalar_one_or_none()
    if row is None:
        row = FreeAgentResourceCache(resource_key=key, payload_json=text)
        db.add(row)
    else:
        row.payload_json = text
    await db.flush()


async def get_cached_report(db: AsyncSession, key: str) -> dict | None:
    result = await db.execute(
        select(FreeAgentResourceCache).where(FreeAgentResourceCache.resource_key == key)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return json.loads(row.payload_json)


async def distributable_profit_from_freeagent(db: AsyncSession) -> dict:
    pl = await get_cached_report(db, "pl_summary_ytd")
    if pl is None:
        return {
            "source": "freeagent",
            "available": False,
            "message": "Run FreeAgent report sync first — no cached P&L.",
        }
    retained = _extract_retained_profit(pl)
    return {
        "source": "freeagent",
        "available": retained is not None,
        "distributable_profit_gbp": float(retained) if retained is not None else None,
        "provisional": False,
        "message": (
            "From FreeAgent P&L retained profit carried forward — confirm with accountant before dividends."
            if retained is not None
            else "FreeAgent P&L did not include retained profit field — use accountant figures."
        ),
    }


async def outstanding_invoices_summary(db: AsyncSession) -> dict:
    result = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE])
        )
    )
    rows = list(result.scalars().all())
    total = sum((i.total_inc_vat_gbp - i.amount_paid_gbp for i in rows), Decimal("0"))
    overdue = [i for i in rows if i.status == InvoiceStatus.OVERDUE]
    return {
        "count": len(rows),
        "outstanding_gbp": float(total),
        "overdue_count": len(overdue),
    }