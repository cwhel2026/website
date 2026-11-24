from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Customer, Enquiry
from app.models.finance import Invoice, InvoiceStatus, Payment
from app.models.quotation import Quotation, QuotationStatus
from app.services.finance.profitability import territory_profitability


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
        select(func.count()).select_from(Enquiry).where(Enquiry.created_at >= since)
    )
    quotations = await db.scalar(
        select(func.count()).select_from(Quotation).where(Quotation.created_at >= since)
    )
    accepted = await db.scalar(
        select(func.count())
        .select_from(Quotation)
        .where(Quotation.created_at >= since, Quotation.status == QuotationStatus.ACCEPTED)
    )
    invoices = await db.scalar(
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.created_at >= since, Invoice.status != InvoiceStatus.VOID)
    )
    collected = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount_gbp), 0)).where(Payment.paid_at >= since)
    )
    quoted_sum = await db.scalar(
        select(func.coalesce(func.sum(Quotation.total_inc_vat_gbp), 0)).where(
            Quotation.created_at >= since
        )
    )
    customers = await db.scalar(
        select(func.count()).select_from(Customer).where(Customer.created_at >= since)
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


async def regional_analytics(db: AsyncSession) -> dict:
    territories = await territory_profitability(db)
    return {
        "territories": [t.__dict__ for t in territories],
        "note": "Figures from recorded quotes and expenses only — no forecasts fabricated.",
    }