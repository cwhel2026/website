import secrets
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking_payment import BookingDeposit
from app.models.finance import Invoice, InvoiceLine, InvoiceStatus
from app.models.quotation import Quotation


async def create_invoice_from_quotation(
    db: AsyncSession,
    quotation: Quotation,
    customer_id: UUID,
    job_id: UUID | None = None,
) -> Invoice:
    # Serialize all draft creation for the same quotation.
    await db.refresh(quotation, with_for_update=True)
    existing = await db.execute(
        select(Invoice).where(
            Invoice.quotation_id == quotation.id,
            Invoice.status != InvoiceStatus.VOID,
        ).order_by(Invoice.created_at).limit(2)
    )
    invoices = list(existing.scalars().all())
    if invoices:
        if len(invoices) != 1 or invoices[0].customer_id != customer_id or invoices[0].job_id != job_id:
            raise ValueError("Existing invoice requires owner review before creating another")
        return invoices[0]
    net = quotation.subtotal_ex_vat_gbp
    vat = quotation.vat_gbp
    gross = quotation.total_inc_vat_gbp
    if job_id:
        deposit = await db.scalar(select(BookingDeposit).where(BookingDeposit.job_id == job_id))
        if deposit:
            deposit_invoice = await db.get(Invoice, deposit.invoice_id)
            if (not deposit_invoice or deposit_invoice.customer_id != customer_id
                    or deposit_invoice.job_id != job_id):
                raise ValueError("Deposit invoice requires owner review")
            if deposit_invoice.status == InvoiceStatus.PAID:
                if (deposit_invoice.amount_paid_gbp != deposit_invoice.total_inc_vat_gbp
                        or deposit_invoice.total_inc_vat_gbp * 100 != deposit.amount_pence
                        or gross * 100 != deposit.total_pence):
                    raise ValueError("Deposit amounts require owner review")
                net -= deposit_invoice.subtotal_ex_vat_gbp
                vat -= deposit_invoice.vat_gbp
                gross -= deposit_invoice.total_inc_vat_gbp
                if min(net, vat, gross) < 0 or net + vat != gross:
                    raise ValueError("Invalid remaining invoice balance")
                if gross == 0:
                    raise ValueError("Job already fully paid; no balance invoice required")
            elif deposit_invoice.status != InvoiceStatus.VOID:
                raise ValueError("Settle or void the deposit invoice before creating a final invoice")
    today = date.today()
    inv = Invoice(
        invoice_number=f"INV-{date.today().strftime('%Y%m')}-{secrets.token_hex(6).upper()}",
        customer_id=customer_id,
        job_id=job_id,
        quotation_id=quotation.id,
        status=InvoiceStatus.DRAFT,
        issue_date=today,
        due_date=today + timedelta(days=14),
        subtotal_ex_vat_gbp=net,
        vat_gbp=vat,
        total_inc_vat_gbp=gross,
        vat_charged=quotation.vat_charged,
        vat_rate_percent=quotation.vat_rate_percent,
    )
    db.add(inv)
    await db.flush()
    db.add(
        InvoiceLine(
            invoice_id=inv.id,
            description="Exterior surface restoration (remaining balance where applicable)",
            quantity=Decimal("1"),
            unit_price_gbp=net,
            line_total_gbp=net,
        )
    )
    return inv