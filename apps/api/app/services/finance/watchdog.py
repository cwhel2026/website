"""Proactive financial issue detection — feeds Telegram outbox."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.finance import Invoice, InvoiceStatus
from app.services.compliance.engine import upcoming_reminders
from app.services.finance.freeagent_adapter import freeagent_status
from app.services.finance.tax_reserves import compute_tax_reserves
from app.services.remuneration.directors_loan import loan_balance


async def run_financial_watchdog(db: AsyncSession) -> list[dict]:
    issues: list[dict] = []
    fa = await freeagent_status(db)
    if fa.state.name == "ERROR":
        issues.append(
            {
                "severity": "high",
                "code": "freeagent_error",
                "title": "FreeAgent connection failed",
                "detail": fa.message,
            }
        )
    elif fa.can_sync and fa.last_sync_at:
        age = datetime.now(UTC) - fa.last_sync_at.replace(tzinfo=UTC if fa.last_sync_at.tzinfo else UTC)
        if age > timedelta(days=3):
            issues.append(
                {
                    "severity": "medium",
                    "code": "stale_freeagent",
                    "title": "Accounting data is stale",
                    "detail": f"Last sync {int(age.days)} days ago.",
                }
            )

    reserves = await compute_tax_reserves(db)
    if reserves.get("is_provisional"):
        issues.append(
            {
                "severity": "medium",
                "code": "provisional_reserves",
                "title": "Tax reserves are provisional",
                "detail": reserves.get("plain_english", ""),
            }
        )

    raw_rec = reserves.get("recommended_reserve_gbp")
    rec = float(raw_rec) if raw_rec is not None else 0.0
    if raw_rec is None:
        issues.append(
            {
                "severity": "medium",
                "code": "tax_reserve_unknown",
                "title": "Tax reserve cannot be calculated yet",
                "detail": "Not enough confirmed income and expense data to estimate a reserve.",
            }
        )
    elif rec > 0:
        issues.append(
            {
                "severity": "low",
                "code": "tax_reserve_reminder",
                "title": "Review tax reserves",
                "detail": f"Planning reserve £{rec:.2f} — not money moved yet.",
            }
        )

    vat = reserves.get("vat_monitor") or {}
    if vat.get("registration_may_be_required"):
        issues.append(
            {
                "severity": "high",
                "code": "vat_registration_risk",
                "title": "VAT registration may be required",
                "detail": vat.get("plain_english", ""),
            }
        )

    compliance = await upcoming_reminders(db, within_days=30)
    for ob in compliance:
        if ob["days_left"] <= 14:
            issues.append(
                {
                    "severity": "high" if ob["days_left"] <= 7 else "medium",
                    "code": f"compliance_{ob['slug']}",
                    "title": ob["title"],
                    "detail": f"Due {ob['due_date']} — {ob['why_it_matters']}",
                }
            )

    reviews = await db.execute(
        select(BookkeepingReviewItem).where(
            BookkeepingReviewItem.status == ReviewItemStatus.PENDING,
            BookkeepingReviewItem.receipt_required.is_(True),
        )
    )
    pending_receipts = len(list(reviews.scalars().all()))
    if pending_receipts:
        issues.append(
            {
                "severity": "medium",
                "code": "missing_receipts",
                "title": "Missing receipts",
                "detail": f"{pending_receipts} bank lines need receipts.",
            }
        )

    inv = await db.execute(
        select(Invoice).where(
            Invoice.status == InvoiceStatus.OVERDUE,
            Invoice.due_date < date.today(),
        )
    )
    overdue = len(list(inv.scalars().all()))
    if overdue:
        issues.append(
            {
                "severity": "medium",
                "code": "overdue_invoices",
                "title": "Overdue customer invoices",
                "detail": f"{overdue} invoices overdue.",
            }
        )

    loan = await loan_balance(db)
    if loan.get("balance_gbp", 0) > 0:
        issues.append(
            {
                "severity": "high",
                "code": "directors_loan",
                "title": "Director loan balance",
                "detail": loan.get("plain_english", ""),
            }
        )

    return issues