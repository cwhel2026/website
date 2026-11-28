"""Live settlement adapter. Not wired to sandbox reconciliation or enabled routes."""
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import select
from app.models.booking_payment import BookingDeposit
from app.models.finance import Invoice, InvoiceStatus, Payment, SyncSource
from app.models.jobs import Job
from app.services.audit import record_audit


async def record_verified_live_deposit(db, deposit_id, *, verified_payment, live_verified=False):
    # This adapter is intentionally unavailable until live provider verification is implemented.
    if not live_verified:
        raise ValueError("Live provider verification required")
    row = await db.get(BookingDeposit, deposit_id)
    if not row:
        raise ValueError("Deposit not found")
    await db.scalar(select(Job).where(Job.id == row.job_id).with_for_update())
    await db.refresh(row, with_for_update=True)
    if not row.provider_payment_id or not row.confirmed_at or row.status != "confirmed":
        raise ValueError("Confirmed linked deposit required")
    if (verified_payment.get("id") != row.provider_payment_id
            or verified_payment.get("currency") != "GBP"
            or str(verified_payment.get("amount")) != str(row.amount_pence)
            or verified_payment.get("status") not in {"confirmed", "paid_out"}):
        raise ValueError("Provider payment mismatch")
    invoice = await db.get(Invoice, row.invoice_id, with_for_update=True)
    amount = Decimal(row.amount_pence) / 100
    if not invoice or invoice.job_id != row.job_id or invoice.total_inc_vat_gbp != amount:
        raise ValueError("Invoice mismatch")
    ident = uuid5(NAMESPACE_URL, "surfacecoat:gocardless:" + row.provider_payment_id)
    existing = await db.get(Payment, ident)
    if existing:
        if existing.invoice_id != invoice.id or existing.amount_gbp != amount or invoice.status != InvoiceStatus.PAID:
            raise ValueError("Existing payment requires review")
        return existing
    if invoice.status not in {InvoiceStatus.DRAFT, InvoiceStatus.SENT, InvoiceStatus.OVERDUE} or invoice.amount_paid_gbp != 0:
        raise ValueError("Invoice already settled or requires review")
    payment = Payment(id=ident, invoice_id=invoice.id, amount_gbp=amount,
                      paid_at=row.confirmed_at, method="gocardless",
                      reference=row.provider_payment_id, source=SyncSource.MANUAL)
    db.add(payment)
    invoice.amount_paid_gbp = amount
    invoice.status = InvoiceStatus.PAID
    await db.flush()
    await record_audit(db, actor_type="system", actor_id="gocardless",
                       action="booking.deposit_settled", entity_type="invoice",
                       entity_id=invoice.id, detail={"payment_id": str(payment.id)})
    return payment
