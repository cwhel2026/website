"""Full-funnel attribution — provisional until finance links complete."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Enquiry
from app.models.finance import Invoice, InvoiceStatus
from app.models.jobs import Job, JobStatus
from app.models.marketing import AttributionEvent, RegionalCampaign
from app.models.quotation import Quotation, QuotationStatus


async def marketing_funnel_attribution(db: AsyncSession, *, days: int = 90) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    touches = await db.scalar(
        select(func.count()).select_from(AttributionEvent).where(AttributionEvent.landed_at >= since)
    )
    linked_enquiries = await db.scalar(
        select(func.count())
        .select_from(AttributionEvent)
        .where(AttributionEvent.landed_at >= since, AttributionEvent.enquiry_id.isnot(None))
    )
    quotes = await db.scalar(
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
    booked_jobs = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.created_at >= since, Job.status.notin((JobStatus.CANCELLED,)))
    )
    completed = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.updated_at >= since, Job.status == JobStatus.COMPLETED)
    )
    invoiced = await db.scalar(
        select(func.coalesce(func.sum(Invoice.total_inc_vat_gbp), 0)).where(
            Invoice.created_at >= since, Invoice.status != InvoiceStatus.VOID
        )
    )
    paid = await db.scalar(
        select(func.coalesce(func.sum(Invoice.total_inc_vat_gbp), 0)).where(
            Invoice.created_at >= since, Invoice.status == InvoiceStatus.PAID
        )
    )
    spend = await db.scalar(
        select(func.coalesce(func.sum(RegionalCampaign.spent_gbp), 0)).where(
            RegionalCampaign.updated_at >= since
        )
    )
    spend_d = Decimal(str(spend or 0))
    paid_d = Decimal(str(paid or 0))

    return {
        "window_days": days,
        "attribution_touches": int(touches or 0),
        "attribution_linked_enquiries": int(linked_enquiries or 0),
        "enquiries_total": int(
            await db.scalar(select(func.count()).select_from(Enquiry).where(Enquiry.created_at >= since)) or 0
        ),
        "quotations": int(quotes or 0),
        "quotations_accepted": int(accepted or 0),
        "jobs_booked": int(booked_jobs or 0),
        "jobs_completed": int(completed or 0),
        "invoiced_gbp": float(invoiced or 0),
        "collected_revenue_gbp": float(paid_d),
        "advertising_spend_gbp": float(spend_d),
        "cost_per_enquiry_gbp": float(spend_d / touches) if touches else None,
        "cost_per_accepted_quote_gbp": float(spend_d / accepted) if accepted else None,
        "roas_collected": float(paid_d / spend_d) if spend_d > 0 else None,
        "revenue_quality": "collected_only — quotations not counted as revenue",
        "attribution_uncertainty": "Cross-channel dedupe and campaign→job link incomplete",
    }