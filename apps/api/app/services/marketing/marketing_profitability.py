"""Marketing ROI — joins spend, attribution, and quotation funnel (provisional attribution)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import AttributionEvent, RegionalCampaign
from app.models.quotation import Quotation, QuotationStatus


async def marketing_profitability_snapshot(db: AsyncSession, *, days: int = 30) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    spend = await db.scalar(
        select(func.coalesce(func.sum(RegionalCampaign.spent_gbp), 0)).where(
            RegionalCampaign.updated_at >= since
        )
    )
    leads = await db.scalar(
        select(func.count()).select_from(AttributionEvent).where(AttributionEvent.landed_at >= since)
    )
    quotes = await db.scalar(
        select(func.count()).select_from(Quotation).where(Quotation.created_at >= since)
    )
    accepted = await db.scalar(
        select(func.count())
        .select_from(Quotation)
        .where(
            Quotation.created_at >= since,
            Quotation.status == QuotationStatus.ACCEPTED,
        )
    )
    quoted_value = await db.scalar(
        select(func.coalesce(func.sum(Quotation.total_inc_vat_gbp), 0)).where(
            Quotation.created_at >= since,
            Quotation.status == QuotationStatus.ACCEPTED,
        )
    )
    spend_d = Decimal(str(spend or 0))
    cpl = float(spend_d / leads) if leads else None
    cpq = float(spend_d / quotes) if quotes else None
    conv = (accepted / quotes * 100) if quotes else None
    return {
        "window_days": days,
        "advertising_spend_gbp": float(spend_d),
        "attribution_events": int(leads or 0),
        "quotations": int(quotes or 0),
        "quotations_accepted": int(accepted or 0),
        "quoted_revenue_gbp": float(quoted_value or 0),
        "cost_per_lead_gbp": cpl,
        "cost_per_quotation_gbp": cpq,
        "quotation_conversion_rate_pct": conv,
        "roas_provisional": float(quoted_value or 0) / float(spend_d) if spend_d > 0 else None,
        "attribution_uncertainty": (
            "Attribution events are not always linked to enquiries or jobs — treat ROAS as provisional."
        ),
        "missing": ["invoice-level margin", "deduplicated cross-platform attribution"],
    }