"""Owner Telegram outbox and quotation delivery trace."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.crm import Customer, CustomerProperty, Enquiry, OwnerFollowUp
from app.models.notifications import NotificationOutbox, NotificationPriority, OutboxStatus
from app.models.quotation import Quotation
from app.models.user import User
from app.services.notifications.outbox import deliver_telegram_outbox_item, enqueue_notification, process_pending_telegram
from app.services.quote_conversion import recover_outstanding_quote_alerts

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/outbox")
async def list_outbox(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(select(NotificationOutbox).order_by(NotificationOutbox.created_at.desc()).limit(50))
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "title": row.title,
            "category": row.category,
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "attempts": row.attempts,
            "last_error": row.last_error,
            "dedupe_key": row.dedupe_key,
            "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.post("/outbox/{item_id}/retry")
async def retry_outbox(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    item = await db.get(NotificationOutbox, item_id, with_for_update=True)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if item.channel != "telegram" or item.status == OutboxStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Notification cannot be retried")
    if item.status == OutboxStatus.DELIVERED:
        return {"id": str(item.id), "delivered": True, "status": item.status.value, "last_error": item.last_error}
    item.status = OutboxStatus.PENDING
    delivered = await deliver_telegram_outbox_item(db, item)
    await db.commit()
    return {"id": str(item.id), "delivered": delivered, "status": item.status.value, "last_error": item.last_error}


@router.post("/telegram/test")
async def send_test_telegram(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    settings = get_settings()
    item = await enqueue_notification(
        db,
        channel="telegram",
        title="TEST NOTIFICATION — SurfaceCoat",
        body=(
            "This is a labelled test. Ignore it for revenue, conversion and marketing.\n"
            "If you received this, outbound Telegram from the API is working."
        ),
        category="test",
        priority=NotificationPriority.HIGH,
        dedupe_key=None,
        payload={"kind": "manual_test"},
    )
    delivered = await deliver_telegram_outbox_item(db, item)
    await db.commit()
    return {
        "delivered": delivered,
        "outbox_id": str(item.id),
        "status": item.status.value if hasattr(item.status, "value") else str(item.status),
        "last_error": item.last_error,
        "bot_token_set": bool(settings.telegram_bot_token),
        "alert_chat_ids": len(settings.telegram_alert_chat_ids),
    }


@router.post("/telegram/recover")
async def recover_telegram(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    recovered = await recover_outstanding_quote_alerts(db)
    pending = await process_pending_telegram(db)
    return {"enquiries_requeued": recovered, "delivered_now": pending}


@router.get("/quotations/{reference}")
async def quotation_delivery_trace(
    reference: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    quotation = (
        await db.execute(
            select(Quotation)
            .options(selectinload(Quotation.sections))
            .where(Quotation.reference == reference)
        )
    ).scalar_one_or_none()
    if quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    enquiry = await db.get(Enquiry, quotation.enquiry_id) if quotation.enquiry_id else None
    customer = await db.get(Customer, quotation.customer_id)
    prop = await db.get(CustomerProperty, quotation.property_id) if quotation.property_id else None
    follow_ups = []
    outbox = []
    if enquiry is not None:
        follow_ups = list(
            (
                await db.execute(select(OwnerFollowUp).where(OwnerFollowUp.enquiry_id == enquiry.id))
            ).scalars().all()
        )
        outbox = list(
            (
                await db.execute(
                    select(NotificationOutbox).where(
                        NotificationOutbox.dedupe_key == f"quote-conversion:{enquiry.id}:{enquiry.intention}"
                    )
                )
            ).scalars().all()
        )
    return {
        "quotation": {
            "id": str(quotation.id),
            "reference": quotation.reference,
            "total_gbp": str(quotation.total_inc_vat_gbp),
            "surface_type": quotation.surface_type.value if quotation.surface_type else None,
            "is_test": bool(quotation.is_test),
            "customer_id": str(quotation.customer_id),
            "property_id": str(quotation.property_id) if quotation.property_id else None,
            "enquiry_id": str(quotation.enquiry_id) if quotation.enquiry_id else None,
        },
        "customer": {
            "id": str(customer.id) if customer else None,
            "full_name": customer.full_name if customer else None,
            "email": customer.email if customer else None,
            "phone": customer.phone if customer else None,
            "is_test": bool(customer.is_test) if customer else None,
        },
        "property": {
            "id": str(prop.id) if prop else None,
            "address": ", ".join(
                part for part in ([prop.address_line1, prop.town, prop.postcode] if prop else []) if part
            ),
        },
        "enquiry": {
            "id": str(enquiry.id) if enquiry else None,
            "intention": enquiry.intention if enquiry else None,
            "priority": enquiry.priority if enquiry else None,
            "stage": enquiry.stage.value if enquiry and enquiry.stage else None,
            "telegram_notified": bool(enquiry.telegram_notified) if enquiry else False,
            "is_test": bool(enquiry.is_test) if enquiry else None,
        },
        "follow_ups": [
            {"id": str(row.id), "kind": row.kind, "title": row.title, "status": row.status}
            for row in follow_ups
        ],
        "telegram_outbox": [
            {
                "id": str(row.id),
                "status": row.status.value if hasattr(row.status, "value") else str(row.status),
                "attempts": row.attempts,
                "last_error": row.last_error,
                "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
            }
            for row in outbox
        ],
        "jobs_created": False,
        "appointment_confirmed": False,
    }


@router.post("/quotations/{reference}/mark-test")
async def mark_quotation_test(
    reference: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    quotation = (
        await db.execute(select(Quotation).where(Quotation.reference == reference))
    ).scalar_one_or_none()
    if quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    quotation.is_test = True
    if quotation.enquiry_id:
        enquiry = await db.get(Enquiry, quotation.enquiry_id)
        if enquiry:
            enquiry.is_test = True
    customer = await db.get(Customer, quotation.customer_id)
    if customer:
        customer.is_test = True
    await db.commit()
    return {"reference": reference, "is_test": True}
