"""Scheduled financial reports — store records + Telegram summaries."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.company import CompanyProfile
from app.models.freeagent_cache import FinancialReportRecord
from app.services.analytics_service import revenue_and_expense_summary
from app.services.compliance.engine import upcoming_reminders
from app.services.finance.cashflow import multi_horizon_cashflow, simple_cashflow_forecast
from app.services.finance.distributable_reserves import compute_distributable_reserves
from app.services.finance.freeagent_reports import get_cached_report, outstanding_invoices_summary
from app.services.finance.tax_reserves import compute_tax_reserves
from app.services.finance.watchdog import run_financial_watchdog
from app.services.notifications.outbox import enqueue_notification
from app.services.remuneration.optimizer import RemunerationInputs, optimise_remuneration
from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief


async def _company_desired_net(db: AsyncSession) -> Decimal:
    result = await db.execute(select(CompanyProfile).limit(1))
    profile = result.scalar_one_or_none()
    if profile and profile.director_desired_monthly_net_gbp:
        return profile.director_desired_monthly_net_gbp
    return Decimal("3000")


async def _store_report(
    db: AsyncSession,
    period: str,
    title: str,
    payload: dict,
    *,
    dashboard_path: str = "/dashboard/finance-hub",
) -> FinancialReportRecord:
    record = FinancialReportRecord(
        period=period,
        title=title,
        payload_json=json.dumps(payload, default=str),
        dashboard_path=dashboard_path,
    )
    db.add(record)
    await db.flush()
    return record


async def generate_daily_finance_report(db: AsyncSession) -> FinancialReportRecord:
    reserves = await compute_tax_reserves(db)
    issues = await run_financial_watchdog(db)
    urgent = [i for i in issues if i["severity"] == "high"]
    reserve = reserves.get("recommended_reserve_gbp")
    reserve_text = f"£{reserve:.2f}" if reserve is not None else "unknown — reconciliation required"
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "tax_reserves": reserves,
        "urgent_issues": urgent,
        "plain_english": (
            f"Morning finance check: planning reserve {reserve_text}. "
            f"{len(urgent)} urgent items." + (" Data provisional." if reserves.get("is_provisional") else "")
        ),
    }
    return await _store_report(db, "daily", "Daily finance briefing", payload, dashboard_path="/dashboard/tax-centre")


async def generate_weekly_finance_report(db: AsyncSession) -> FinancialReportRecord:
    rev_exp = await revenue_and_expense_summary(db)
    reserves = await compute_tax_reserves(db)
    cashflow = await simple_cashflow_forecast(db, days=30)
    invoices = await outstanding_invoices_summary(db)
    reviews = await db.execute(
        select(BookkeepingReviewItem).where(
            BookkeepingReviewItem.status == ReviewItemStatus.PENDING,
            BookkeepingReviewItem.receipt_required.is_(True),
        )
    )
    missing_receipts = len(list(reviews.scalars().all()))
    from app.services.finance.profitability import territory_profitability

    territories = await territory_profitability(db)
    payload = {
        "revenue_gbp": rev_exp.get("revenue_gbp"),
        "expenses_gbp": rev_exp.get("expenses_gbp"),
        "profit_estimate_gbp": rev_exp.get("profit_estimate_gbp"),
        "tax_reserves": reserves,
        "cashflow_30d": cashflow,
        "invoices": invoices,
        "missing_receipts": missing_receipts,
        "basis": rev_exp.get("basis"),
        "is_provisional": True,
        "territory_profitability": [
            {"territory": r.territory_code, "estimated_quoted_contribution_gbp": float(r.estimated_profit_gbp)}
            for r in territories[:12]
        ],
        "plain_english": (
            f"Weekly snapshot: revenue £{rev_exp.get('revenue_gbp', 0):.0f}, "
            f"expenses £{rev_exp.get('expenses_gbp', 0):.0f}, "
            f"{missing_receipts} receipt(s) still needed."
        ),
    }
    return await _store_report(db, "weekly", "Weekly finance report", payload)


async def generate_monthly_finance_report(db: AsyncSession) -> FinancialReportRecord:
    reserves = await compute_tax_reserves(db)
    dist = await compute_distributable_reserves(db)
    distributable = dist.get("available_distributable_gbp")
    desired = await _company_desired_net(db)
    profit = None
    pl_cached = await get_cached_report(db, "pl_summary_ytd")
    if pl_cached:
        from app.services.finance.freeagent_reports import _extract_net_profit_before_tax

        np = _extract_net_profit_before_tax(pl_cached)
        if np is not None:
            profit = np
    obligation = Decimal(str(reserves.get("recommended_reserve_gbp") or 0))
    opt = None
    blocked_reason = None
    if reserves.get("has_unknown_liabilities"):
        blocked_reason = "Tax liabilities incomplete; remuneration recommendations withheld."
    elif dist.get("blocked"):
        blocked_reason = dist.get("message") or "Reserves unavailable"
    elif profit is None or distributable is None:
        blocked_reason = "Verified profit and reserves unavailable."
    else:
        blocked_reason = "Verified available company cash required before remuneration recommendations."
    pl = await get_cached_report(db, "pl_summary_ytd")
    bs = await get_cached_report(db, "balance_sheet_latest")
    ct_forecast = corporation_tax_with_marginal_relief(profit) if profit is not None and profit > 0 else {"corporation_tax_gbp": None}
    deadlines = await upcoming_reminders(db, within_days=90)
    cashflow = await multi_horizon_cashflow(db)
    adequacy = reserves.get("recommended_reserve_gbp")
    adequacy_text = f"£{adequacy:.0f}" if adequacy is not None else "unknown"
    payload = {
        "management_accounts": {
            "pl_ytd_cached": pl is not None,
            "balance_sheet_cached": bs is not None,
            "revenue_gbp": (await revenue_and_expense_summary(db)).get("revenue_gbp"),
        },
        "company_profitability_gbp": float(profit) if profit is not None else None,
        "corporation_tax_forecast": ct_forecast,
        "personal_tax_note": "Use director-pay optimiser after accountant confirms reserves.",
        "tax_reserves": reserves,
        "reserve_adequacy_gbp": adequacy,
        "recommended_remuneration": opt.get("recommended") if opt else None,
        "remuneration_blocked_reason": blocked_reason,
        "distributable_reserves": dist,
        "statutory_deadlines": deadlines[:15],
        "cashflow_scenarios": cashflow,
        "requires_accountant_review": True,
        "plain_english": (
            blocked_reason
            if blocked_reason
            else (
                f"Monthly accounts pack ready. Suggested reserve {adequacy_text}. "
                f"Target take-home £{desired}/mo — open director pay for scenarios."
            )
        ),
    }
    return await _store_report(
        db, "monthly", "Monthly management report", payload, dashboard_path="/dashboard/director-pay"
    )


async def generate_annual_finance_report(db: AsyncSession) -> FinancialReportRecord:
    dist = await compute_distributable_reserves(db)
    reserves = await compute_tax_reserves(db)
    payload = {
        "year_end_checklist": [
            "Confirm FreeAgent year-end lock with accountant",
            "Reconcile all bank transactions",
            "Review director loan balance",
            "VAT and corporation tax estimates",
            "Dividend vouchers and board minutes",
            "Export CSV packs for accountant",
            "Verify receipt volume backup off-platform",
        ],
        "reconciliation_checks": [
            "FreeAgent bank feed vs statements",
            "P&L vs balance sheet retained profit",
            "VAT return supporting receipts",
        ],
        "distributable_reserves": dist,
        "tax_reserves": reserves,
        "exports": [
            "/api/v1/finance/accountant/export/invoices.csv",
            "/api/v1/finance/accountant/export/expenses.csv",
            "/api/v1/finance/accountant/export/bank.csv",
        ],
        "accountant_handover": "Download CSV exports + grant accountant role user.",
        "plain_english": (
            "Year-end pack lists reconciliation steps — nothing is filed automatically. "
            "Book accountant review before locking accounts."
        ),
    }
    return await _store_report(
        db,
        "annual",
        "Year-end preparation pack",
        payload,
        dashboard_path="/dashboard/finance-hub",
    )


async def deliver_report_telegram(db: AsyncSession, record: FinancialReportRecord) -> dict:
    settings = get_settings()
    base = (settings.public_dashboard_base_url or settings.public_api_base_url or "").rstrip("/")
    link = f"{base}{record.dashboard_path}" if base else record.dashboard_path
    body = f"{record.title}\n\nOpen dashboard: {link}\n\n{json.loads(record.payload_json).get('plain_english', 'See dashboard for detail.')}"[:3500]
    await enqueue_notification(
        db,
        channel="telegram",
        title=record.title,
        body=body,
        category=f"finance_report_{record.period}",
        dedupe_key=f"fin-report:{record.period}:{record.id}",
        priority="normal",
    )
    record.telegram_sent = False
    await db.flush()
    return {"queued": True, "outbox_category": f"finance_report_{record.period}", "telegram_sent": False}


async def mark_finance_report_delivered(db: AsyncSession, dedupe_key: str) -> None:
    if not dedupe_key.startswith("fin-report:"):
        return
    parts = dedupe_key.split(":")
    if len(parts) < 3:
        return
    try:
        from uuid import UUID

        report_id = UUID(parts[2])
    except ValueError:
        return
    record = await db.get(FinancialReportRecord, report_id)
    if record:
        record.telegram_sent = True
        await db.flush()


async def annual_report_idempotency_key(db: AsyncSession) -> str | None:
    result = await db.execute(select(CompanyProfile).limit(1))
    profile = result.scalar_one_or_none()
    if not profile or not profile.accounting_reference_month or not profile.accounting_reference_day:
        return None
    today = date.today()
    if today.month != profile.accounting_reference_month or today.day != profile.accounting_reference_day:
        return None
    return f"annual:{today.year}"


async def should_run_annual_report(db: AsyncSession) -> bool:
    return (await annual_report_idempotency_key(db)) is not None