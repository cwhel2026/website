from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking_payment import BookingDeposit
from app.services.payments.gocardless import GoCardlessClient


async def reconcile_sandbox_deposit(db: AsyncSession, deposit_id, client: GoCardlessClient) -> str:
    """Verify provider linkage and amount; sandbox must never settle real invoices."""
    row = await db.get(BookingDeposit, deposit_id, with_for_update=True)
    if not row or not row.billing_request_id:
        raise ValueError("Billing request required")
    billing = await client.get_billing_request(row.billing_request_id)
    if billing.get("id") != row.billing_request_id:
        raise ValueError("Billing request mismatch")
    payment_id = billing.get("links", {}).get("payment_request_payment")
    if not payment_id:
        return "awaiting_payment"
    if row.provider_payment_id and row.provider_payment_id != payment_id:
        raise ValueError("Payment identity changed")
    payment = await client.get_payment(payment_id)
    if (payment.get("id") != payment_id or payment.get("currency") != "GBP"
            or str(payment.get("amount")) != str(row.amount_pence)):
        row.status = "review"
        return "review"
    row.provider_payment_id = payment_id
    status = payment.get("status")
    if status in ("confirmed", "paid_out"):
        row.status = "confirmed"
        row.confirmed_at = row.confirmed_at or datetime.now(UTC)
    elif status in ("failed", "cancelled", "charged_back"):
        row.status = "review" if row.confirmed_at else ("failed" if status == "failed" else "cancelled")
    return row.status
