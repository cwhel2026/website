"""Legally available distributable reserves — not bank balance or current-period P&L alone."""

from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.remuneration import DividendProposal, DividendProposalStatus
from app.services.finance.freeagent_reports import _extract_retained_profit, get_cached_report
from app.services.finance.tax_reserves import compute_tax_reserves


def _decimal_from_balance_sheet(bs: dict) -> Decimal | None:
    summary = bs.get("balance_sheet_summary") or bs.get("balance_sheet") or bs
    for key in (
        "retained_profit",
        "retained-profit",
        "accumulated_profits",
        "capital_and_reserves",
    ):
        val = summary.get(key)
        if val is not None:
            try:
                return Decimal(str(val))
            except Exception:
                continue
    return None


async def compute_distributable_reserves(db: AsyncSession) -> dict:
    pl = await get_cached_report(db, "pl_summary_ytd")
    bs = await get_cached_report(db, "balance_sheet_latest")
    reserves = await compute_tax_reserves(db)

    retained_pl = _extract_retained_profit(pl or {}) if pl else None
    retained_bs = _decimal_from_balance_sheet(bs or {}) if bs else None

    if retained_pl is None and retained_bs is None:
        return {
            "available": False,
            "blocked": True,
            "message": (
                "No FreeAgent retained profit or balance sheet figures cached — "
                "sync reports and confirm with accountant before dividends."
            ),
            "requires_accountant_review": True,
        }

    if retained_pl is not None and retained_bs is not None:
        distributable = min(retained_pl, retained_bs)
        mismatch = abs(retained_pl - retained_bs) > Decimal("1")
    elif retained_pl is not None:
        distributable = retained_pl
        mismatch = False
    else:
        distributable = retained_bs or Decimal("0")
        mismatch = False

    pending_div = await db.execute(
        select(func.coalesce(func.sum(DividendProposal.amount_gbp), 0)).where(
            DividendProposal.status.in_(
                [DividendProposalStatus.AWAITING_APPROVAL, DividendProposalStatus.APPROVED]
            )
        )
    )
    dividends_reserved = Decimal(str(pending_div.scalar() or 0))

    ct_est = Decimal(str(reserves.get("corporation_tax_gbp", 0)))
    after_tax = max(Decimal("0"), distributable - ct_est - dividends_reserved)

    notes: list[str] = []
    if mismatch:
        notes.append(
            "P&L retained profit differs from balance sheet — accountant must reconcile before dividends."
        )
    if reserves.get("is_provisional"):
        notes.append("Local tax reserve estimate is provisional.")

    return {
        "available": True,
        "blocked": mismatch or reserves.get("is_provisional"),
        "distributable_profit_gbp": float(distributable),
        "after_tax_and_pending_dividends_gbp": float(after_tax),
        "retained_profit_pl_gbp": float(retained_pl) if retained_pl is not None else None,
        "retained_bs_gbp": float(retained_bs) if retained_bs is not None else None,
        "pending_dividends_gbp": float(dividends_reserved),
        "estimated_corporation_tax_gbp": float(ct_est),
        "mismatch_pl_vs_bs": mismatch,
        "requires_accountant_review": True,
        "plain_english": (
            "Distributable reserves use FreeAgent accumulated figures minus estimated corporation tax "
            "and approved-but-unpaid dividend proposals — never bank balance alone."
        ),
        "notes": notes,
    }