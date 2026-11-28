import secrets
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    today = date.today()
    inv = Invoice(
        invoice_number=f"INV-{date.today().strftime('%Y%m')}-{secrets.token_hex(6).upper()}",
        customer_id=customer_id,
        job_id=job_id,
        quotation_id=quotation.id,
        status=InvoiceStatus.DRAFT,
        issue_date=today,
        due_date=today + timedelta(days=14),
        subtotal_ex_vat_gbp=quotation.subtotal_ex_vat_gbp,
        vat_gbp=quotation.vat_gbp,
        total_inc_vat_gbp=quotation.total_inc_vat_gbp,
        vat_charged=quotation.vat_charged,
        vat_rate_percent=quotation.vat_rate_percent,
    )
    db.add(inv)
    await db.flush()
    db.add(
        InvoiceLine(
            invoice_id=inv.id,
            description="Exterior surface restoration (per quotation)",
            quantity=Decimal("1"),
            unit_price_gbp=quotation.subtotal_ex_vat_gbp,
            line_total_gbp=quotation.subtotal_ex_vat_gbp,
        )
    )
    return inv