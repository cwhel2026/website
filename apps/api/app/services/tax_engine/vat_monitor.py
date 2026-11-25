from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile, VatStatus
from app.models.finance import Expense, Invoice, InvoiceStatus
from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


async def rolling_vat_taxable_turnover(db: AsyncSession, *, as_of: date | None = None) -> dict:
    """Uses invoiced revenue (ex VAT) over rolling 12 months — provisioning estimate, not HMRC filing."""
    today = as_of or date.today()
    window_start = today - timedelta(days=365)

    inv = await db.execute(
        select(Invoice).where(
            Invoice.issue_date >= window_start,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.PAID, InvoiceStatus.OVERDUE]),
        )
    )
    turnover = Decimal("0")
    for row in inv.scalars().all():
        turnover += row.subtotal_ex_vat_gbp

    exp = await db.execute(select(Expense).where(Expense.expense_date >= window_start))
    expenses = sum((e.amount_gbp for e in exp.scalars().all()), Decimal("0"))

    profile = await db.execute(select(CompanyProfile).limit(1))
    prof = profile.scalar_one_or_none()
    threshold = ACTIVE_RULES.vat_registration_threshold_gbp
    vat_status = prof.vat_status.value if prof else "unknown"

    pct_of_threshold = float((turnover / threshold * Decimal("100")).quantize(Decimal("0.1"))) if threshold else 0
    must_register = turnover > threshold and (
        not prof or prof.vat_status not in (VatStatus.REGISTERED, VatStatus.APPLIED)
    )

    return {
        "window_start": window_start.isoformat(),
        "window_end": today.isoformat(),
        "taxable_turnover_gbp": float(turnover),
        "threshold_gbp": float(threshold),
        "percent_of_threshold": pct_of_threshold,
        "registration_may_be_required": must_register,
        "vat_status": vat_status,
        "expenses_in_window_gbp": float(expenses),
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "plain_english": (
            "You may need to register for VAT if taxable turnover exceeds the statutory threshold "
            "over a rolling 12-month period. This estimate uses invoices in this system only."
            if must_register
            else "Turnover is below the compulsory registration threshold on current data — keep monitoring monthly."
        ),
        "provisional": True,
    }