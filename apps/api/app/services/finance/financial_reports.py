"""Scheduled financial reports — store records + Telegram summaries."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.freeagent_cache import FinancialReportRecord
from app.services.analytics_service import revenue_and_expense_summary
from app.services.finance.cashflow import simple_cashflow_forecast
from app.services.finance.freeagent_reports import (
    distributable_profit_from_freeagent,
    get_cached_report,
    outstanding_invoices_summary,
)
from app.services.finance.tax_reserves import compute_tax_reserves
from app.services.finance.watchdog import run_financial_watchdog
from app.services.notifications.outbox import enqueue_notification
from app.services.remuneration.optimizer import RemunerationInputs, optimise_remuneration


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
    payload = {
        "revenue_gbp": rev_exp.get("revenue_gbp"),
        "expenses_gbp": rev_exp.get("expenses_gbp"),
        "profit_estimate_gbp": rev_exp.get("profit_estimate_gbp"),
        "tax_reserves": reserves,
        "cashflow_30d": cashflow,
        "invoices": invoices,
        "missing_receipts": missing_receipts,
        "plain_english": (
            f"Weekly snapshot: revenue £{rev_exp.get('revenue_gbp', 0):.0f}, "
            f"expenses £{rev_exp.get('expenses_gbp', 0):.0f}, "
            f"{missing_receipts} receipt(s) still needed."
        ),
    }
    return await _store_report(db, "weekly", "Weekly finance report", payload)


async def generate_monthly_finance_report(db: AsyncSession) -> FinancialReportRecord:
    reserves = await compute_tax_reserves(db)
    dist = await distributable_profit_from_freeagent(db)
    distributable = dist.get("distributable_profit_gbp")
    profit = distributable if distributable is not None else reserves.get("profit_estimate_gbp", 0)
    opt = optimise_remuneration(
        RemunerationInputs(
            desired_monthly_net_gbp=__import__("decimal").Decimal("3000"),
            annual_company_profit_before_remuneration_gbp=__import__("decimal").Decimal(str(profit or 0)),
            distributable_reserves_gbp=__import__("decimal").Decimal(str(distributable or profit or 0)),
            company_cash_gbp=__import__("decimal").Decimal(str(distributable or profit or 0)),
        )
    )
    pl = await get_cached_report(db, "pl_summary_ytd")
    bs = await get_cached_report(db, "balance_sheet_latest")
    payload = {
        "management_accounts": {"pl_ytd": pl is not None, "balance_sheet": bs is not None},
        "tax_reserves": reserves,
        "recommended_remuneration": opt.get("recommended"),
        "distributable_profit": dist,
        "requires_accountant_review": True,
    }
    return await _store_report(db, "monthly", "Monthly finance report", payload, dashboard_path="/dashboard/director-pay")


async def generate_annual_finance_report(db: AsyncSession) -> FinancialReportRecord:
    payload = {
        "year_end_checklist": [
            "Confirm FreeAgent year-end lock with accountant",
            "Reconcile all bank transactions",
            "Review director loan balance",
            "VAT and corporation tax estimates",
            "Dividend vouchers and board minutes",
            "Export CSV packs for accountant",
        ],
        "exports": ["/api/v1/finance/accountant/export/invoices.csv", "/api/v1/finance/accountant/export/expenses.csv"],
    }
    return await _store_report(db, "annual", "Year-end preparation pack", payload)


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