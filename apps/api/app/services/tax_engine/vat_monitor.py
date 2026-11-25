from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile, VatStatus
from app.models.finance import Invoice, InvoiceStatus
from app.services.tax_engine.rules_uk_ltd import rules_for_date


async def rolling_vat_taxable_turnover(db: AsyncSession, *, as_of: date | None = None) -> dict:
    """Rolling 12-month turnover plus forward test — not a VAT return."""
    today = as_of or date.today()
    rules = rules_for_date(today)
    window_start = today - timedelta(days=365)

    inv = await db.execute(
        select(Invoice).where(
            Invoice.issue_date >= window_start,
            Invoice.issue_date <= today,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.PAID, InvoiceStatus.OVERDUE]),
        )
    )
    turnover = Decimal("0")
    for row in inv.scalars().all():
        turnover += row.subtotal_ex_vat_gbp

    forward_end = today + timedelta(days=30 * rules.vat_registration_forward_months)
    future = await db.execute(
        select(Invoice).where(
            Invoice.issue_date > today,
            Invoice.issue_date <= forward_end,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE]),
        )
    )
    forward_turnover = sum((i.subtotal_ex_vat_gbp for i in future.scalars().all()), Decimal("0"))

    profile = await db.execute(select(CompanyProfile).limit(1))
    prof = profile.scalar_one_or_none()
    threshold = rules.vat_registration_threshold_gbp
    vat_status = prof.vat_status.value if prof else "unknown"

    rolling_exceeds = turnover > threshold
    forward_projected = turnover + forward_turnover
    forward_exceeds = forward_projected > threshold
    must_register = (rolling_exceeds or forward_exceeds) and (
        not prof or prof.vat_status not in (VatStatus.REGISTERED, VatStatus.APPLIED)
    )

    return {
        "window_start": window_start.isoformat(),
        "window_end": today.isoformat(),
        "forward_window_end": forward_end.isoformat(),
        "taxable_turnover_gbp": float(turnover),
        "forward_invoiced_gbp": float(forward_turnover),
        "forward_projected_turnover_gbp": float(forward_projected),
        "threshold_gbp": float(threshold),
        "rolling_over_threshold": rolling_exceeds,
        "forward_test_over_threshold": forward_exceeds,
        "registration_may_be_required": must_register,
        "vat_status": vat_status,
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "sources": list(rules.sources),
        "verified_on": rules.verified_on,
        "plain_english": (
            "Compulsory VAT registration may be required — confirm with accountant and HMRC."
            if must_register
            else "Below threshold on rolling and forward invoice data in this system — keep monitoring."
        ),
        "provisional": prof is None,
        "data_complete": prof is not None,
    }