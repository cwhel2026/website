"""Periodic sandbox verification, independent of webhook delivery order."""
from sqlalchemy import select

from app.config import get_settings
from app.models.booking_payment import BookingDeposit
from app.services.payments.gocardless import GoCardlessClient, GoCardlessError
from app.services.payments.reconcile import reconcile_sandbox_deposit


async def sweep_sandbox_deposits(session_factory, *, limit: int = 50) -> dict:
    settings = get_settings()
    if (settings.environment.lower() == "production" or not settings.gocardless_enabled
            or settings.gocardless_environment != "sandbox" or not settings.gocardless_access_token):
        return {"enabled": False, "checked": 0, "errors": 0}
    client = GoCardlessClient(settings.gocardless_access_token, sandbox=True)
    async with session_factory() as db:
        ids = list(await db.scalars(select(BookingDeposit.id).where(
            BookingDeposit.billing_request_id.is_not(None),
            BookingDeposit.status.in_(("pending", "confirmed", "review"))
        ).order_by(BookingDeposit.created_at.desc()).limit(max(1, min(limit, 100)))))
    checked = errors = 0
    for deposit_id in ids:
        async with session_factory() as db:
            try:
                await reconcile_sandbox_deposit(db, deposit_id, client)
                await db.commit()
                checked += 1
            except (GoCardlessError, ValueError):
                await db.rollback()
                errors += 1
    return {"enabled": True, "checked": checked, "errors": errors}
