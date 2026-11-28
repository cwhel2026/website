from datetime import datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking_payment import BookingDeposit
from app.models.finance import Invoice, InvoiceLine, InvoiceStatus
from app.models.jobs import Job, JobStatus
from app.models.quotation import Quotation, QuotationStatus
from app.services.finance.booking_amounts import booking_amounts
from app.services.payments.gocardless import pounds_to_pence


async def draft_deposit(db: AsyncSession, job_id: UUID, percent: Decimal) -> BookingDeposit:
    job = await db.get(Job, job_id, with_for_update=True)
    if not job or not job.quotation_id:
        raise ValueError("Job with accepted quotation required")
    if job.status not in (JobStatus.DRAFT, JobStatus.AWAITING_PREP_BOOKING):
        raise ValueError("Job is not awaiting booking")
    quote = await db.get(Quotation, job.quotation_id, with_for_update=True)
    if not quote or quote.is_test or quote.status != QuotationStatus.ACCEPTED or quote.customer_id != job.customer_id:
        raise ValueError("Accepted non-test quotation required")
    net, vat, gross = booking_amounts(quote.subtotal_ex_vat_gbp, quote.vat_gbp, percent)
    total = pounds_to_pence(quote.total_inc_vat_gbp)
    if total != pounds_to_pence(quote.subtotal_ex_vat_gbp + quote.vat_gbp):
        raise ValueError("Quotation totals require review")
    amount = pounds_to_pence(gross)
    existing = await db.scalar(select(BookingDeposit).where(BookingDeposit.job_id == job.id))
    if existing:
        if existing.amount_pence != amount or existing.total_pence != total:
            raise ValueError("Existing deposit requires owner review")
        return existing
    today = datetime.now(ZoneInfo("Europe/London")).date()
    invoice = Invoice(invoice_number="DEP-" + job.id.hex[:28], customer_id=job.customer_id,
                      job_id=job.id, status=InvoiceStatus.DRAFT, issue_date=today, due_date=today,
                      subtotal_ex_vat_gbp=net, vat_gbp=vat, total_inc_vat_gbp=gross,
                      vat_charged=quote.vat_charged, vat_rate_percent=quote.vat_rate_percent,
                      notes="Booking deposit; deduct confirmed payment from final invoice.")
    db.add(invoice)
    await db.flush()
    db.add(InvoiceLine(invoice_id=invoice.id, description="Booking deposit", quantity=Decimal("1"),
                       unit_price_gbp=net, line_total_gbp=net))
    deposit = BookingDeposit(job_id=job.id, invoice_id=invoice.id, total_pence=total,
                             amount_pence=amount, status="draft")
    db.add(deposit)
    await db.flush()
    return deposit
