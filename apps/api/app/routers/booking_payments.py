from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.booking_payment import BookingDeposit
from app.models.user import User
from app.services.audit import record_audit
from app.services.payments.booking import draft_deposit

router = APIRouter(prefix="/booking-payments", tags=["booking-payments"])
DB = Annotated[AsyncSession, Depends(get_db)]


class DepositRequest(BaseModel):
    percentage: Decimal = Field(default=Decimal("10"), gt=0, le=100, decimal_places=2)


def serialize(row: BookingDeposit) -> dict:
    return {"id": str(row.id), "job_id": str(row.job_id),
            "invoice_id": str(row.invoice_id) if row.invoice_id else None,
            "total_pence": row.total_pence, "amount_pence": row.amount_pence,
            "status": row.status, "payment_url": row.payment_url}


@router.post("/jobs/{job_id}/deposit")
async def create_deposit(job_id: UUID, body: DepositRequest, db: DB,
                         user: Annotated[User, Depends(get_current_admin_writer)]) -> dict:
    try:
        row = await draft_deposit(db, job_id, body.percentage)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(409, str(exc)) from None
    await record_audit(db, actor_type="user", actor_id=str(user.id),
                       action="booking.deposit_draft", entity_id=row.id)
    result = serialize(row)
    await db.commit()
    return result


@router.get("/jobs/{job_id}/deposit")
async def get_deposit(job_id: UUID, db: DB,
                      _: Annotated[User, Depends(get_current_admin)]) -> dict:
    row = await db.scalar(select(BookingDeposit).where(BookingDeposit.job_id == job_id))
    if not row:
        raise HTTPException(404, "Booking deposit not found")
    return serialize(row)


@router.post("/jobs/{job_id}/payment-link")
async def payment_link(job_id: UUID, db: DB,
                       user: Annotated[User, Depends(get_current_admin_writer)]) -> dict:
    from app.config import get_settings
    from app.services.payments.gocardless import GoCardlessClient, GoCardlessError
    from app.models.finance import Invoice, InvoiceStatus

    settings = get_settings()
    if settings.environment.lower() == "production" or not settings.gocardless_enabled or settings.gocardless_environment != "sandbox":
        raise HTTPException(409, "Sandbox payments must be explicitly enabled; live payments are not available")
    if not all((settings.gocardless_access_token, settings.gocardless_webhook_secret,
                settings.gocardless_redirect_uri, settings.gocardless_exit_uri)):
        raise HTTPException(409, "GoCardless configuration incomplete")
    row = await db.scalar(select(BookingDeposit).where(BookingDeposit.job_id == job_id).with_for_update())
    if not row or row.status not in ("draft", "pending"):
        raise HTTPException(409, "Eligible booking deposit required")
    if row.payment_url:
        return serialize(row)
    invoice = await db.get(Invoice, row.invoice_id, with_for_update=True)
    if not invoice or invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(409, "Draft deposit invoice required")
    client = GoCardlessClient(settings.gocardless_access_token, sandbox=True)
    try:
        if not row.billing_request_id:
            result = await client.create_billing_request(
                amount_pence=row.amount_pence, reference=invoice.invoice_number,
                idempotency_key=f"deposit-{row.id.hex}")
            row.billing_request_id = result["billing_requests"]["id"]
        result = await client.create_billing_request_flow(
            billing_request_id=row.billing_request_id,
            redirect_uri=settings.gocardless_redirect_uri, exit_uri=settings.gocardless_exit_uri,
            idempotency_key=f"flow-{row.id.hex}")
        url = result["billing_request_flows"]["authorisation_url"]
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("Invalid provider URL")
    except (GoCardlessError, KeyError, ValueError):
        await db.rollback()
        raise HTTPException(502, "Payment link creation failed; retry with the same deposit") from None
    row.payment_url = url
    row.status = "pending"
    await record_audit(db, actor_type="user", actor_id=str(user.id),
                       action="booking.sandbox_payment_link", entity_id=row.id)
    response = serialize(row)
    await db.commit()
    return response


@router.post("/gocardless/webhook")
async def payment_webhook(request: Request, db: DB) -> dict:
    import json
    from sqlalchemy.dialects.postgresql import insert
    from app.config import get_settings
    from app.models.booking_payment import BookingPaymentEvent
    from app.services.payments.gocardless import verify_webhook_signature

    settings = get_settings()
    if settings.environment.lower() == "production" or not settings.gocardless_enabled or settings.gocardless_environment != "sandbox":
        raise HTTPException(503, "Payment integration disabled")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 1024 * 1024:
            raise HTTPException(413, "Webhook too large")
    if not verify_webhook_signature(bytes(body), request.headers.get("Webhook-Signature"),
                                    settings.gocardless_webhook_secret or ""):
        raise HTTPException(401, "Invalid webhook signature")
    try:
        events = json.loads(body)["events"]
        if not isinstance(events, list) or len(events) > 1000:
            raise ValueError()
        for event in events:
            event_id = event["id"]
            action = event["action"]
            resource = event["resource_type"]
            payment_id = event.get("links", {}).get("payment")
            if not all(isinstance(v, str) and v for v in (event_id, action, resource)):
                raise ValueError()
            if len(event_id) > 100 or len(action) > 80:
                raise ValueError()
            if payment_id is not None and (not isinstance(payment_id, str) or len(payment_id) > 100):
                raise ValueError()
            if resource != "payments":
                continue
            await db.execute(insert(BookingPaymentEvent).values(
                event_id=event_id, action=action, payment_id=payment_id
            ).on_conflict_do_nothing(index_elements=["event_id"]))
    except (ValueError, KeyError, TypeError, AttributeError):
        await db.rollback()
        raise HTTPException(400, "Invalid webhook payload") from None
    await db.commit()
    return {"received": True}


@router.post("/jobs/{job_id}/reconcile")
async def reconcile_deposit(job_id: UUID, db: DB,
                            user: Annotated[User, Depends(get_current_admin_writer)]) -> dict:
    from app.config import get_settings
    from app.services.payments.gocardless import GoCardlessClient, GoCardlessError
    from app.services.payments.reconcile import reconcile_sandbox_deposit

    settings = get_settings()
    if (settings.environment.lower() == "production" or not settings.gocardless_enabled
            or settings.gocardless_environment != "sandbox" or not settings.gocardless_access_token):
        raise HTTPException(409, "Reconciliation requires a non-production sandbox")
    row = await db.scalar(select(BookingDeposit).where(BookingDeposit.job_id == job_id))
    if not row:
        raise HTTPException(404, "Booking deposit not found")
    try:
        state = await reconcile_sandbox_deposit(db, row.id, GoCardlessClient(settings.gocardless_access_token))
    except ValueError:
        await db.rollback()
        raise HTTPException(409, "Deposit requires review") from None
    except GoCardlessError:
        await db.rollback()
        raise HTTPException(502, "Provider verification unavailable") from None
    await record_audit(db, actor_type="user", actor_id=str(user.id),
                       action="booking.sandbox_reconcile", entity_id=row.id,
                       detail={"state": state})
    result = serialize(row)
    await db.commit()
    return result
