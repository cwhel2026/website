"""Legally distributable reserves — requires reconciled FreeAgent evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.remuneration import DividendProposal, DividendProposalStatus
from app.services.finance.freeagent_adapter import freeagent_status
from app.services.finance.freeagent_reports import _extract_retained_profit, get_cached_report


def _retained_from_balance_sheet(bs: dict) -> Decimal | None:
    summary = bs.get("balance_sheet_summary") or bs.get("balance_sheet") or bs
    for key in ("retained_profit", "retained-profit", "accumulated_profits", "retained_earnings"):
        val = summary.get(key)
        if val is not None:
            try:
                return Decimal(str(val))
            except Exception:
                continue
    return None


async def compute_distributable_reserves(db: AsyncSession) -> dict:
    fa = await freeagent_status(db)
    pl = await get_cached_report(db, "pl_summary_ytd")
    bs = await get_cached_report(db, "balance_sheet_latest")

    retained_pl = _extract_retained_profit(pl or {}) if pl else None
    retained_bs = _retained_from_balance_sheet(bs or {}) if bs else None

    stale = True
    if fa.last_sync_at:
        stale = datetime.now(UTC) - fa.last_sync_at > timedelta(days=7)

    if retained_pl is None and retained_bs is None:
        return {
            "available": False,
            "blocked": True,
            "message": "No retained profit figures from FreeAgent — run report sync and obtain accountant sign-off.",
            "requires_accountant_review": True,
            "data_stale": stale,
        }

    if retained_pl is not None and retained_bs is not None:
        if abs(retained_pl - retained_bs) > Decimal("5"):
            return {
                "available": False,
                "blocked": True,
                "message": "P&L retained profit does not match balance sheet — reconcile before dividends.",
                "retained_profit_pl_gbp": float(retained_pl),
                "retained_bs_gbp": float(retained_bs),
                "requires_accountant_review": True,
                "data_stale": stale,
            }
        distributable = retained_pl
    elif retained_pl is not None:
        return {
            "available": False,
            "blocked": True,
            "message": "Balance sheet retained profit missing — single-source insufficient for dividends.",
            "retained_profit_pl_gbp": float(retained_pl),
            "requires_accountant_review": True,
            "data_stale": stale,
        }
    else:
        return {
            "available": False,
            "blocked": True,
            "message": "P&L retained profit missing — single-source insufficient for dividends.",
            "retained_bs_gbp": float(retained_bs or 0),
            "requires_accountant_review": True,
            "data_stale": stale,
        }

    pending_div = await db.execute(
        select(func.coalesce(func.sum(DividendProposal.amount_gbp), 0)).where(
            DividendProposal.status.in_(
                [DividendProposalStatus.AWAITING_APPROVAL, DividendProposalStatus.APPROVED]
            )
        )
    )
    dividends_reserved = Decimal(str(pending_div.scalar() or 0))

    # Retained profit from FreeAgent is typically post-corporation-tax — do not deduct CT again.
    available_now = max(Decimal("0"), distributable - dividends_reserved)

    projected_ytd = retained_pl
    notes = [
        "Figures are accumulated realised profits per FreeAgent — not bank balance.",
        "Corporation tax not deducted again from retained profit.",
    ]
    if stale:
        notes.append("FreeAgent sync older than 7 days — treat as stale.")

    return {
        "available": True,
        "blocked": stale,
        "blocked_reason": "Stale FreeAgent data — refresh sync and confirm with accountant." if stale else None,
        "distributable_profit_gbp": float(distributable),
        "available_distributable_gbp": float(available_now),
        "projected_ytd_profit_gbp": float(projected_ytd),
        "pending_dividends_gbp": float(dividends_reserved),
        "retained_profit_pl_gbp": float(retained_pl) if retained_pl is not None else None,
        "retained_bs_gbp": float(retained_bs) if retained_bs is not None else None,
        "requires_accountant_review": True,
        "data_stale": stale,
        "plain_english": (
            f"~£{available_now:.0f} potentially distributable after pending dividend proposals — accountant must confirm."
        ),
        "notes": notes,
    }