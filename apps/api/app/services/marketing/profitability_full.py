"""Marketing profitability with finance links — nulls explicit."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, ExpenseCategory, Invoice, InvoiceStatus
from app.models.jobs import Job, JobStatus
from app.models.marketing import AttributionEvent, RegionalCampaign
from app.models.quotation import Quotation, QuotationStatus
from app.services.marketing.attribution_journey import marketing_funnel_attribution


async def marketing_profitability_full(db: AsyncSession, *, days: int = 90) -> dict:
    funnel = await marketing_funnel_attribution(db, days=days)
    since = datetime.now(UTC) - timedelta(days=days)

    ad_spend = funnel.get("advertising_spend_gbp")
    if ad_spend is None:
        ad_spend_unknown = True
        ad_spend = None
    else:
        ad_spend_unknown = False

    job_costs = await db.scalar(
        select(func.coalesce(func.sum(Expense.amount_gbp), 0)).where(
            Expense.expense_date >= since.date(),
            Expense.category == ExpenseCategory.ADVERTISING,
        )
    )
    paid_jobs = (
        await db.execute(
            select(Job, Invoice)
            .join(Invoice, Invoice.job_id == Job.id)
            .where(Job.status == JobStatus.COMPLETED, Invoice.status == InvoiceStatus.PAID, Invoice.created_at >= since)
        )
    ).all()
    collected = Decimal("0")
    for _, inv in paid_jobs:
        if inv.total_inc_vat_gbp is not None:
            collected += inv.total_inc_vat_gbp

    cac = None
    if funnel.get("quotations_accepted") and ad_spend is not None and funnel["quotations_accepted"] > 0:
        cac = float(Decimal(str(ad_spend)) / Decimal(funnel["quotations_accepted"]))
    mroi = None
    if ad_spend is not None and float(ad_spend) > 0:
        mroi = float(collected) / float(ad_spend)

    return {
        **funnel,
        "advertising_spend_gbp": ad_spend,
        "advertising_spend_unknown": ad_spend_unknown,
        "expense_advertising_gbp": float(job_costs) if job_costs is not None else None,
        "collected_revenue_paid_jobs_gbp": float(collected) if paid_jobs else 0.0,
        "collected_revenue_note": "Only PAID invoices linked to COMPLETED jobs",
        "customer_acquisition_cost_gbp": cac,
        "marketing_roi": mroi,
        "job_contribution_gbp": None,
        "job_contribution_note": "Direct job cost allocation not fully modelled — null not zero",
        "optimise_for": "profitable_completed_work",
    }