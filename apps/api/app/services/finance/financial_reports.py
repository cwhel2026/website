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
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "tax_reserves": reserves,
        "urgent_issues": urgent,
        "plain_english": (
            f"Morning finance check: planning reserve £{reserves.get('recommended_reserve_gbp', 0):.2f}. "
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
    marketing = sum(
        1 for _ in territories
    )  # placeholder count; detail in payload
    payload = {
        "revenue_gbp": rev_exp.get("revenue_gbp"),
        "expenses_gbp": rev_exp.get("expenses_gbp"),
        "profit_estimate_gbp": rev_exp.get("profit_estimate_gbp"),
        "tax_reserves": reserves,
        "cashflow_30d": cashflow,
        "invoices": invoices,
        "missing_receipts": missing_receipts,
        "marketing_territories_tracked": marketing,
        "territory_profitability": [
            {"territory": r.territory_code, "profit_gbp": float(r.estimated_profit_gbp)}
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
    distributable = dist.get("after_tax_and_pending_dividends_gbp") or dist.get("distributable_profit_gbp")
    desired = await _company_desired_net(db)
    profit = Decimal(str(reserves.get("profit_estimate_gbp", 0)))
    opt = None
    blocked_reason = None
    if dist.get("blocked"):
        blocked_reason = dist.get("message") or "Reserves unavailable"
    else:
        opt = optimise_remuneration(
            RemunerationInputs(
                desired_monthly_net_gbp=desired,
                annual_company_profit_before_remuneration_gbp=profit,
                distributable_reserves_gbp=Decimal(str(distributable or 0)),
                company_cash_gbp=Decimal(str(distributable or 0)),
            )
        )
    pl = await get_cached_report(db, "pl_summary_ytd")
    bs = await get_cached_report(db, "balance_sheet_latest")
    ct_forecast = corporation_tax_with_marginal_relief(profit)
    deadlines = await upcoming_reminders(db, within_days=90)
    cashflow = await multi_horizon_cashflow(db)
    adequacy = reserves.get("recommended_reserve_gbp", 0)
    payload = {
        "management_accounts": {
            "pl_ytd_cached": pl is not None,
            "balance_sheet_cached": bs is not None,
            "revenue_gbp": (await revenue_and_expense_summary(db)).get("revenue_gbp"),
        },
        "company_profitability_gbp": float(profit),
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
                f"Monthly accounts pack ready. Suggested reserve £{adequacy:.0f}. "
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


async def deliver_report_telegram(db: AsyncSession, record: FinancialReportRecord) -> bool:
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
    record.telegram_sent = True
    await db.flush()
    return True


async def should_run_annual_report(db: AsyncSession) -> bool:
    result = await db.execute(select(CompanyProfile).limit(1))
    profile = result.scalar_one_or_none()
    today = date.today()
    if profile and profile.accounting_reference_month and profile.accounting_reference_day:
        if today.month == profile.accounting_reference_month and today.day == profile.accounting_reference_day:
            return True
    # Default: last month of UK financial year prep window
    return today.month == 3 and today.day == 1