from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Customer, Enquiry
from app.models.finance import Expense, Invoice, InvoiceStatus, Payment
from app.models.quotation import Quotation, QuotationStatus
from app.services.finance.profitability import territory_profitability


def issued_business_invoices():
    return (
        select(Invoice.id)
        .join(Customer, Customer.id == Invoice.customer_id)
        .outerjoin(Quotation, Quotation.id == Invoice.quotation_id)
        .where(
            Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.VOID]),
            Customer.is_test.is_(False),
            or_(Invoice.quotation_id.is_(None), Quotation.is_test.is_(False)),
        )
    )


@dataclass
class AnalyticsSnapshot:
    period_days: int
    enquiries: int
    quotations: int
    quotes_accepted: int
    invoices_sent: int
    revenue_collected_gbp: Decimal
    quoted_revenue_gbp: Decimal
    quote_conversion_rate: float
    unique_customers: int


async def build_analytics_snapshot(db: AsyncSession, days: int = 30) -> AnalyticsSnapshot:
    since = datetime.now(UTC) - timedelta(days=days)

    enquiries = await db.scalar(
        select(func.count()).select_from(Enquiry).where(Enquiry.created_at >= since, Enquiry.is_test.is_(False))
    )
    quotations = await db.scalar(
        select(func.count()).select_from(Quotation).where(Quotation.created_at >= since, Quotation.is_test.is_(False))
    )
    accepted = await db.scalar(
        select(func.count())
        .select_from(Quotation)
        .where(
            Quotation.created_at >= since,
            Quotation.status == QuotationStatus.ACCEPTED,
            Quotation.is_test.is_(False),
        )
    )
    invoices = await db.scalar(
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.created_at >= since, Invoice.id.in_(issued_business_invoices()))
    )
    collected = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount_gbp), 0)).where(Payment.paid_at >= since, Payment.paid_at <= datetime.now(UTC), Payment.invoice_id.in_(issued_business_invoices()))
    )
    quoted_sum = await db.scalar(
        select(func.coalesce(func.sum(Quotation.total_inc_vat_gbp), 0)).where(
            Quotation.created_at >= since, Quotation.is_test.is_(False)
        )
    )
    customers = await db.scalar(
        select(func.count()).select_from(Customer).where(Customer.created_at >= since, Customer.is_test.is_(False))
    )

    enq = enquiries or 0
    quotes = quotations or 0
    conv = (quotes / enq * 100.0) if enq > 0 else 0.0

    return AnalyticsSnapshot(
        period_days=days,
        enquiries=enq,
        quotations=quotes,
        quotes_accepted=accepted or 0,
        invoices_sent=invoices or 0,
        revenue_collected_gbp=Decimal(str(collected or 0)).quantize(Decimal("0.01")),
        quoted_revenue_gbp=Decimal(str(quoted_sum or 0)).quantize(Decimal("0.01")),
        quote_conversion_rate=round(conv, 2),
        unique_customers=customers or 0,
    )


async def revenue_and_expense_summary(db: AsyncSession, days: int = 7) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    collected = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount_gbp), 0)).where(Payment.paid_at >= since, Payment.paid_at <= datetime.now(UTC), Payment.invoice_id.in_(issued_business_invoices()))
    )
    expense_sum = await db.scalar(
        select(func.coalesce(func.sum(Expense.amount_gbp), 0)).where(Expense.expense_date >= since.date(), Expense.expense_date <= datetime.now(UTC).date())
    )
    revenue = Decimal(str(collected or 0))
    expenses = Decimal(str(expense_sum or 0))
    return {
        "period_days": days,
        "revenue_gbp": float(revenue),
        "expenses_gbp": float(expenses),
        "profit_estimate_gbp": float(revenue - expenses),
        "basis": "Recorded payments linked to issued non-test invoices less recorded expenses; not accrual profit or reconciled bank cash.",
        "is_provisional": True,
    }


async def regional_analytics(db: AsyncSession) -> dict:
    territories = await territory_profitability(db)
    return {
        "territories": [t.__dict__ for t in territories],
        "note": "Figures from recorded quotes and expenses only — no forecasts fabricated.",
    }