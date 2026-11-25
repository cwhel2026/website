"""FreeAgent payroll — read-only sync; no RTI submission."""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.freeagent_cache import FreeAgentResourceCache
from app.services.finance import freeagent_client
from app.services.finance.freeagent_adapter import ensure_fresh_token, freeagent_status, get_connection_row


async def sync_payroll_status(db: AsyncSession) -> dict:
    settings = get_settings()
    status = await freeagent_status(db)
    if not status.can_sync:
        return {"ok": False, "message": status.message}
    row = await get_connection_row(db)
    if row is None:
        return {"ok": False, "message": "Not connected"}

    year = date.today().year
    try:
        token = await ensure_fresh_token(db, row, settings)
        payload = await freeagent_client.fetch_payroll_year(settings, token, year)
    except Exception as exc:
        return {
            "ok": False,
            "message": str(exc),
            "guidance": (
                "Enable FreeAgent payroll and reconnect OAuth with permission level 7+. "
                "RTI filing is done in FreeAgent — this system only reads status."
            ),
        }

    key = f"payroll_{year}"
    result = await db.execute(select(FreeAgentResourceCache).where(FreeAgentResourceCache.resource_key == key))
    cache = result.scalar_one_or_none()
    text = json.dumps(payload, default=str)
    if cache is None:
        db.add(FreeAgentResourceCache(resource_key=key, payload_json=text))
    else:
        cache.payload_json = text
    await db.flush()

    periods = payload.get("periods") or []
    payments = payload.get("payments") or []
    return {
        "ok": True,
        "year": year,
        "periods": len(periods),
        "payments": payments,
        "plain_english": (
            f"FreeAgent reports {len(periods)} payroll period(s) for {year}. "
            "Submit pay runs in FreeAgent — watch payment due dates below."
        ),
        "submission_via_api": False,
    }


async def payroll_guidance() -> dict:
    return {
        "provider": "freeagent_builtin",
        "rti_submission_supported_here": False,
        "steps": [
            "Set up payroll in FreeAgent (Settings → Payroll).",
            "Add yourself as an employee/director with correct NI treatment.",
            "Each month: run payroll in FreeAgent and file FPS to HMRC from FreeAgent.",
            "Use Director pay in this dashboard for planning only until accountant approves.",
        ],
        "sources": ["https://dev.freeagent.com/docs/payroll"],
    }