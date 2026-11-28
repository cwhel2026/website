"""Turn a saved quotation into a customer request without confirming a booking."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.crm import Customer, CustomerProperty, Enquiry, OwnerFollowUp, PipelineStage
from app.models.notifications import NotificationPriority
from app.models.quotation import Quotation, QuotationSection
from app.models.quotation_photo import QuotePhoto, QuotePhotoSet
from app.services.notifications.outbox import deliver_telegram_outbox_item, enqueue_notification

logger = logging.getLogger(__name__)

READY_TO_BOOK = "ready_to_book"
CALLBACK_REQUESTED = "callback_requested"
ESTIMATE_REQUESTED = "estimate_requested"
FLEXIBLE_BOOKING = "flexible_booking"
INTENTIONS = {READY_TO_BOOK, CALLBACK_REQUESTED, ESTIMATE_REQUESTED, FLEXIBLE_BOOKING}

INTENTION_LABELS = {
    FLEXIBLE_BOOKING: "Flexible booking discount request",
    READY_TO_BOOK: "Booking request",
    CALLBACK_REQUESTED: "Callback requested",
    ESTIMATE_REQUESTED: "Estimate requested",
}

FOLLOW_UP_TITLES = {
    FLEXIBLE_BOOKING: "Contact customer to agree discounted price and area-matched dates",
    READY_TO_BOOK: "Contact customer to agree a restoration visit",
    CALLBACK_REQUESTED: "Return the customer's callback request",
    ESTIMATE_REQUESTED: "Follow up the saved estimate",
}

CUSTOMER_HEADING = "Thank you for choosing SurfaceCoat"

BOOKING_SUPPORTING = (
    "We've received your booking request and will be in touch shortly to arrange your restoration."
)
CALLBACK_SUPPORTING = "We've received your callback request and will be in touch shortly."
ESTIMATE_SUPPORTING = "We've received your estimate request and saved your details."

BOOKING_STEPS = [
    "We review your details and photographs.",
    "We contact you to agree a visit.",
    "Nothing is booked until we confirm it with you.",
]


def apply_customer_intention(enquiry: Enquiry, body) -> None:
    intention = getattr(body, "intention", None) or ESTIMATE_REQUESTED
    if intention not in INTENTIONS:
        raise HTTPException(status_code=400, detail="Choose booking, flexible booking, callback, or email.")
    enquiry.intention = intention
    enquiry.utm_source = getattr(body, "source", None) or enquiry.utm_source
    enquiry.utm_medium = getattr(body, "utm_medium", None) or enquiry.utm_medium
    enquiry.utm_campaign = getattr(body, "campaign", None) or enquiry.utm_campaign
    if intention in {READY_TO_BOOK, FLEXIBLE_BOOKING}:
        enquiry.priority = "high"
        enquiry.stage = PipelineStage.BOOKING_PENDING
        enquiry.callback_status = "not_applicable"
    elif intention == CALLBACK_REQUESTED:
        enquiry.priority = "high"
        enquiry.stage = PipelineStage.AWAITING_INFORMATION
        enquiry.callback_phone = getattr(body, "phone", None)
        enquiry.callback_preferred_time = (getattr(body, "callback_preferred_time", None) or "").strip()
        if enquiry.callback_status != "completed":
            enquiry.callback_status = "open"
    else:
        enquiry.priority = "normal"
        enquiry.stage = PipelineStage.QUOTE_GENERATED
        enquiry.callback_status = "not_applicable"


def customer_next_steps(
    enquiry: Enquiry,
    windows: list[dict] | None = None,
    *,
    email: str,
    photos_attached: bool = False,
    repair_review: bool = False,
) -> str:
    del windows, photos_attached, repair_review
    if enquiry.intention == FLEXIBLE_BOOKING:
        return "We have received your flexible booking request. Our team will contact you to agree your discounted price and dates when we are working in your area."
    if enquiry.intention == READY_TO_BOOK:
        return BOOKING_SUPPORTING
    if enquiry.intention == CALLBACK_REQUESTED:
        when = enquiry.callback_preferred_time or "a time that suits you"
        return f"{CALLBACK_SUPPORTING} We will call around {when}."
    if enquiry.email_delivery == "sent":
        return f"{ESTIMATE_SUPPORTING} We have emailed it to {email}."
    if enquiry.email_delivery == "failed":
        return f"{ESTIMATE_SUPPORTING} The email could not be sent. We still have your details."
    return f"{ESTIMATE_SUPPORTING} We could not email it because email sending is not connected."


def confirmation_steps(enquiry: Enquiry) -> list[str]:
    if enquiry.intention == FLEXIBLE_BOOKING:
        return ["We check dates when we are working in your area.", "We contact you to agree your discounted price and dates.", "Nothing is booked until we confirm it with you."]
    if enquiry.intention == CALLBACK_REQUESTED:
        return [
            "We call you at the time you asked for.",
            "We agree any visit with you on that call.",
            "You can add photographs now or later.",
        ]
    if enquiry.intention == ESTIMATE_REQUESTED:
        return [
            "Your estimate is saved against this reference.",
            "We will contact you if we need anything further.",
            "You can add photographs now or later.",
        ]
    return BOOKING_STEPS


def smtp_configured() -> bool:
    settings = get_settings()
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def _send_smtp(message: EmailMessage) -> None:
    settings = get_settings()
    if not smtp_configured():
        raise RuntimeError("SMTP not configured")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


async def send_estimate_email(
    *,
    to_email: str,
    customer_name: str,
    reference: str,
    total_gbp: str,
    postcode: str,
    included: list[str],
) -> str:
    if not smtp_configured():
        return "not_sent_smtp_unconfigured"
    settings = get_settings()
    lines = "\n".join(f"- {item}" for item in included) or "- Driveway restoration as described"
    message = EmailMessage()
    message["Subject"] = f"Your SurfaceCoat estimate {reference}"
    message["From"] = f"SurfaceCoat Ltd <{settings.outreach_from_email}>"
    message["To"] = to_email
    message.set_content(
        f"Hello {customer_name},\n\n"
        f"Your estimated price for the property at {postcode} is £{total_gbp}.\n\n"
        f"Included:\n{lines}\n\n"
        "This is an estimate. It is not a confirmed booking. "
        "We confirm the final price after checking the measurements on site.\n\n"
        "SurfaceCoat Ltd\n"
        "Restore. Protect. Transform.\n"
    )
    try:
        await asyncio.to_thread(_send_smtp, message)
    except Exception:
        logger.exception("Estimate email failed for %s", reference)
        return "failed"
    return "sent"


def _origin() -> str:
    origin = get_settings().public_origin
    if origin:
        return origin
    return "https://website-production-c21e95cd.up.railway.app"


def _owner_links(photo_token: str | None) -> str:
    base = _origin()
    lines = [
        f"Review quotation: {base}/dashboard/quotations",
        f"Review availability: {base}/dashboard/calendar",
        f"Customer record: {base}/dashboard/customers",
    ]
    if photo_token:
        lines.append(f"Photographs: {base}/quote/photos/{photo_token}")
    return "\n".join(lines)


async def _photo_status(db: AsyncSession, quotation_id: UUID) -> tuple[bool, int]:
    photo_set = (
        await db.execute(select(QuotePhotoSet).where(QuotePhotoSet.quotation_id == quotation_id))
    ).scalar_one_or_none()
    if photo_set is None:
        return False, 0
    count = await db.scalar(select(func.count()).select_from(QuotePhoto).where(QuotePhoto.set_id == photo_set.id))
    return bool(count), int(count or 0)


async def build_owner_alert(
    db: AsyncSession,
    *,
    enquiry: Enquiry,
    quotation: Quotation | None,
    customer: Customer | None,
    prop: CustomerProperty | None,
    photo_token: str | None,
) -> str:
    reference = quotation.reference if quotation else "unreferenced"
    name = customer.full_name if customer else "Unknown"
    email = customer.email if customer else ""
    phone = enquiry.callback_phone or (customer.phone if customer else "") or "not given"
    address_parts = []
    if prop:
        address_parts = [prop.address_line1, prop.address_line2, prop.town, prop.postcode]
    address = ", ".join(part for part in address_parts if part) or "Address not stored"
    surface = (enquiry.surface_type.value if enquiry.surface_type else None) or (
        quotation.surface_type.value if quotation and quotation.surface_type else "unknown"
    )
    area = f"{quotation.total_area_sqm} m²" if quotation else "unknown"
    total = f"£{quotation.total_inc_vat_gbp}" if quotation else "unknown"
    sections = []
    if quotation:
        rows = (
            await db.execute(select(QuotationSection).where(QuotationSection.quotation_id == quotation.id))
        ).scalars().all()
        for row in rows:
            if row.length_m is not None and row.width_m is not None:
                sections.append(f"{row.label}: {row.length_m}m × {row.width_m}m ({row.area_sqm} m²)")
            else:
                sections.append(f"{row.label}: {row.area_sqm} m²")
    measures = "; ".join(sections) or area
    photos_attached, photo_count = await _photo_status(db, quotation.id) if quotation else (False, 0)
    photo_line = f"{photo_count} attached" if photos_attached else "none yet — customer can add later"
    test_line = "TEST RECORD — exclude from revenue and marketing.\n" if enquiry.is_test else ""
    callback_line = ""
    if enquiry.intention == CALLBACK_REQUESTED and enquiry.callback_preferred_time:
        callback_line = f"Preferred call time: {enquiry.callback_preferred_time}\n"
    return (
        f"{test_line}"
        f"Action: {INTENTION_LABELS.get(enquiry.intention or '', 'New quotation')}\n"
        f"Reference: {reference}\n"
        f"Customer: {name}\n"
        f"Phone: {phone}\n"
        f"Email: {email}\n"
        f"Property: {address}\n"
        f"Surface: {surface}\n"
        f"Measurements: {measures}\n"
        f"Estimated value: {total}\n"
        f"Photographs: {photo_line}\n"
        f"{callback_line}"
        "This is a booking request. No appointment is reserved.\n"
        "Review availability in the diary before offering a visit.\n\n"
        f"{_owner_links(photo_token)}"
    )


async def notify_owner(
    db: AsyncSession,
    enquiry: Enquiry,
    *,
    reference: str,
    summary: str,
) -> bool:
    """Always persist an outbox row. Attempt delivery now. Leave pending if the worker is down."""
    label = INTENTION_LABELS.get(enquiry.intention or "", "New quotation")
    priority = NotificationPriority.URGENT if enquiry.intention == READY_TO_BOOK else NotificationPriority.HIGH
    item = await enqueue_notification(
        db,
        channel="telegram",
        title=f"SurfaceCoat · {label} · {reference}",
        body=summary,
        category="quotation",
        priority=priority,
        dedupe_key=f"quote-conversion:{enquiry.id}:{enquiry.intention}",
        payload={"enquiry_id": str(enquiry.id), "reference": reference, "intention": enquiry.intention},
    )
    enquiry.telegram_outbox_id = item.id
    await db.flush()
    try:
        delivered = await deliver_telegram_outbox_item(db, item)
    except Exception:
        logger.exception("Telegram notification failed for %s", reference)
        delivered = False
    enquiry.telegram_notified = bool(delivered)
    return delivered


async def ensure_follow_up(
    db: AsyncSession,
    *,
    enquiry: Enquiry,
    quotation_id: UUID | None,
) -> OwnerFollowUp:
    kind = enquiry.intention or ESTIMATE_REQUESTED
    existing = (
        await db.execute(
            select(OwnerFollowUp).where(OwnerFollowUp.enquiry_id == enquiry.id, OwnerFollowUp.kind == kind)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    row = OwnerFollowUp(
        enquiry_id=enquiry.id,
        quotation_id=quotation_id,
        customer_id=enquiry.customer_id,
        kind=kind,
        title=FOLLOW_UP_TITLES.get(kind, "Follow up quotation"),
        status="open",
        due_at=datetime.now(UTC),
    )
    db.add(row)
    await db.flush()
    return row


async def follow_up_customer_request(
    db: AsyncSession,
    *,
    quotation_id: UUID,
    enquiry: Enquiry,
    body,
    included: list[str],
    two_stage: bool,
    photo_token: str | None = None,
) -> list[dict]:
    del two_stage
    quotation = await db.get(Quotation, quotation_id)
    customer = await db.get(Customer, enquiry.customer_id)
    prop = None
    if quotation and quotation.property_id:
        prop = await db.get(CustomerProperty, quotation.property_id)
    await ensure_follow_up(db, enquiry=enquiry, quotation_id=quotation_id)
    if enquiry.intention == ESTIMATE_REQUESTED and enquiry.email_delivery in {
        "not_requested",
        "not_sent_smtp_unconfigured",
    }:
        total = quotation.total_inc_vat_gbp if quotation else ""
        enquiry.email_delivery = await send_estimate_email(
            to_email=body.email,
            customer_name=body.full_name,
            reference=quotation.reference if quotation else "",
            total_gbp=f"{total}",
            postcode=body.postcode,
            included=included,
        )
    summary = await build_owner_alert(
        db,
        enquiry=enquiry,
        quotation=quotation,
        customer=customer,
        prop=prop,
        photo_token=photo_token,
    )
    await notify_owner(
        db,
        enquiry,
        reference=quotation.reference if quotation else "",
        summary=summary,
    )
    await db.commit()
    await db.refresh(enquiry)
    return []


async def recover_outstanding_quote_alerts(db: AsyncSession) -> int:
    """Re-queue booking alerts that were saved without a delivered Telegram message."""
    rows = (
        await db.execute(
            select(Enquiry).where(
                Enquiry.intention.in_(list(INTENTIONS)),
                Enquiry.telegram_notified.is_(False),
            )
        )
    ).scalars().all()
    recovered = 0
    for enquiry in rows:
        quotation = None
        if enquiry.quotation_id:
            quotation = await db.get(Quotation, enquiry.quotation_id)
        customer = await db.get(Customer, enquiry.customer_id)
        prop = await db.get(CustomerProperty, enquiry.property_id) if enquiry.property_id else None
        photo_set = None
        if quotation:
            photo_set = (
                await db.execute(select(QuotePhotoSet).where(QuotePhotoSet.quotation_id == quotation.id))
            ).scalar_one_or_none()
        await ensure_follow_up(db, enquiry=enquiry, quotation_id=quotation.id if quotation else None)
        summary = await build_owner_alert(
            db,
            enquiry=enquiry,
            quotation=quotation,
            customer=customer,
            prop=prop,
            photo_token=photo_set.token if photo_set else None,
        )
        await notify_owner(
            db,
            enquiry,
            reference=quotation.reference if quotation else "",
            summary=summary,
        )
        recovered += 1
    await db.commit()
    return recovered


def validate_conversion_request(body) -> None:
    intention = getattr(body, "intention", None) or ESTIMATE_REQUESTED
    if intention not in INTENTIONS:
        raise HTTPException(status_code=400, detail="Choose book, callback, or email.")
    if "@" not in body.email or body.email.lower().endswith("@example.com"):
        raise HTTPException(status_code=400, detail="Please enter your email address.")
    if len(body.full_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Please enter your name.")
    if len(body.address_line1.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please enter the property address.")
    phone = (body.phone or "").strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if intention in {READY_TO_BOOK, CALLBACK_REQUESTED, FLEXIBLE_BOOKING} and len(digits) < 8:
        raise HTTPException(status_code=400, detail="Please enter a telephone number.")
    preferred = (getattr(body, "callback_preferred_time", None) or "").strip()
    if intention == CALLBACK_REQUESTED and len(preferred) < 2:
        raise HTTPException(status_code=400, detail="Please tell us when to call.")
