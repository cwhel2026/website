from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, Invoice, InvoiceStatus, Payment, TaxYearSettings


@dataclass
class TaxEstimateResult:
    tax_year: str
    revenue_collected_gbp: Decimal
    expenses_gbp: Decimal
    estimated_profit_gbp: Decimal
    estimated_income_tax_gbp: Decimal
    suggested_reserve_gbp: Decimal
    vat_ytd_turnover_gbp: Decimal
    vat_threshold_gbp: Decimal
    notes: list[str]


async def get_tax_settings(db: AsyncSession) -> TaxYearSettings:
    result = await db.execute(select(TaxYearSettings).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        row = TaxYearSettings()
        db.add(row)
        await db.flush()
    return row


async def estimate_personal_tax(db: AsyncSession) -> TaxEstimateResult:
    """
    Legacy personal tax planning view — Revive My Drive Ltd operates as a UK private company.
    Use /finance/tax/corporation-estimate for company CT planning. NOT HMRC filing software.
    """
    settings = await get_tax_settings(db)
    notes = [
        "Indicative management estimate only — consult your accountant.",
        "Company trades through Revive My Drive Ltd — director salary/dividend via Tax centre (Stage 6).",
        "Does not include student loans, dividends, or other income adjustments.",
    ]

    paid = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_gbp), 0))
    )
    revenue = Decimal(str(paid.scalar() or 0))

    invoiced = await db.execute(
        select(func.coalesce(func.sum(Invoice.total_inc_vat_gbp), 0)).where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.PAID])
        )
    )
    vat_turnover = Decimal(str(invoiced.scalar() or 0))

    exp = await db.execute(select(func.coalesce(func.sum(Expense.amount_gbp), 0)))
    expenses = Decimal(str(exp.scalar() or 0))

    profit = revenue - expenses
    taxable = max(Decimal("0"), profit - settings.personal_allowance_gbp)
    income_tax = taxable * (settings.basic_rate_pct / Decimal("100"))
    income_tax = income_tax.quantize(Decimal("0.01"))

    reserve = (income_tax * Decimal("1.1")).quantize(Decimal("0.01"))

    return TaxEstimateResult(
        tax_year=settings.tax_year_label,
        revenue_collected_gbp=revenue.quantize(Decimal("0.01")),
        expenses_gbp=expenses.quantize(Decimal("0.01")),
        estimated_profit_gbp=profit.quantize(Decimal("0.01")),
        estimated_income_tax_gbp=income_tax,
        suggested_reserve_gbp=reserve,
        vat_ytd_turnover_gbp=vat_turnover.quantize(Decimal("0.01")),
        vat_threshold_gbp=settings.vat_registration_threshold_gbp,
        notes=notes,
    )