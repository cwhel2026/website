"""Turn a saved quotation into a customer request without confirming a booking."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.crm import CustomerProperty, Enquiry, PipelineStage
from app.models.notifications import NotificationPriority
from app.models.quotation import Quotation
from app.models.weather import ProductProfile
from app.services.notifications.outbox import deliver_telegram_outbox_item, enqueue_notification
from app.services.scheduling_engine import propose_two_stage_slots

logger = logging.getLogger(__name__)

LONDON = ZoneInfo("Europe/London")

READY_TO_BOOK = "ready_to_book"
CALLBACK_REQUESTED = "callback_requested"
ESTIMATE_REQUESTED = "estimate_requested"
INTENTIONS = {READY_TO_BOOK, CALLBACK_REQUESTED, ESTIMATE_REQUESTED}

INTENTION_LABELS = {
    READY_TO_BOOK: "Ready to book",
    CALLBACK_REQUESTED: "Callback requested",
    ESTIMATE_REQUESTED: "Estimate requested",
}


def apply_customer_intention(enquiry: Enquiry, body) -> None:
    intention = getattr(body, "intention", None) or ESTIMATE_REQUESTED
    if intention not in INTENTIONS:
        raise HTTPException(status_code=400, detail="Choose book, callback, or email.")
    enquiry.intention = intention
    enquiry.utm_source = getattr(body, "source", None) or enquiry.utm_source
    enquiry.utm_medium = getattr(body, "utm_medium", None) or enquiry.utm_medium
    enquiry.utm_campaign = getattr(body, "campaign", None) or enquiry.utm_campaign
    if intention == READY_TO_BOOK:
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


def customer_next_steps(enquiry: Enquiry, windows: list[dict], *, email: str) -> str:
    if enquiry.intention == READY_TO_BOOK:
        text = (
            "We have your request for the earliest visit. "
            "This is not a confirmed booking. "
            "We will check the diary, travel and weather, then contact you to agree a time."
        )
        if windows:
            when = _format_local(windows[0]["starts"])
            text += f" One possible time to check is {when}. Nothing is reserved until we confirm it with you."
        return text
    if enquiry.intention == CALLBACK_REQUESTED:
        when = enquiry.callback_preferred_time or "a time that suits you"
        return (
            f"We will call you around {when}. "
            "Your visit is not booked. "
            "We will agree any appointment with you on the call."
        )
    if enquiry.email_delivery == "sent":
        return (
            f"We have emailed your estimate to {email}. "
            "We have also saved it. This is not a confirmed booking."
        )
    if enquiry.email_delivery == "failed":
        return (
            "We have saved your estimate. "
            "The email could not be sent. "
            "We still have your details and this is not a confirmed booking."
        )
    return (
        "We have saved your estimate. "
        "We could not email it because email sending is not connected. "
        "We still have your details. This is not a confirmed booking."
    )


def _format_local(value: datetime) -> str:
    local = value.astimezone(LONDON) if value.tzinfo else value.replace(tzinfo=LONDON)
    return local.strftime("%A %d %B at %H:%M")


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
    """Send the estimate only when SMTP is configured. Never reports success otherwise."""
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


async def notify_owner(db: AsyncSession, enquiry: Enquiry, *, reference: str, summary: str) -> bool:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_admin_id_list:
        return False
    label = INTENTION_LABELS.get(enquiry.intention or "", "New quotation")
    priority = NotificationPriority.URGENT if enquiry.intention == READY_TO_BOOK else NotificationPriority.HIGH
    item = await enqueue_notification(
        db,
        channel="telegram",
        title=f"SurfaceCoat · {label}",
        body=f"{reference}\n{summary}",
        category="quotation",
        priority=priority,
        dedupe_key=f"quote-conversion:{enquiry.id}:{enquiry.intention}",
    )
    try:
        return await deliver_telegram_outbox_item(db, item)
    except Exception:
        logger.exception("Telegram notification failed for %s", reference)
        return False


async def suggest_unconfirmed_windows(
    db: AsyncSession,
    *,
    latitude: float | None,
    longitude: float | None,
    two_stage: bool,
) -> list[dict]:
    """Read the diary and weather. Does not insert a job or appointment."""
    if latitude is None or longitude is None:
        return []
    try:
        profile = (
            await db.execute(select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1))
        ).scalar_one_or_none()
        if profile is None:
            return []

        async def _search():
            return await propose_two_stage_slots(
                db,
                lat=float(latitude),
                lon=float(longitude),
                product_profile=profile,
                max_prep_slots=1,
            )

        prep, coat = await asyncio.wait_for(_search(), timeout=8)
    except Exception:
        logger.info("Unconfirmed window search unavailable")
        await db.rollback()
        return []
    windows: list[dict] = []
    if prep:
        windows.append(
            {"label": "Possible cleaning visit", "starts": prep[0].start, "kind": "preparation"}
        )
    if two_stage and coat:
        windows.append(
            {"label": "Possible coating visit", "starts": coat[0].start, "kind": "coating"}
        )
    elif not two_stage and prep:
        windows[0]["label"] = "Possible restoration visit"
        windows[0]["kind"] = "single_visit"
    return windows


async def follow_up_customer_request(
    db: AsyncSession,
    *,
    quotation_id: UUID,
    enquiry: Enquiry,
    body,
    included: list[str],
    two_stage: bool,
) -> list[dict]:
    quotation = await db.get(Quotation, quotation_id)
    prop = None
    if quotation and quotation.property_id:
        prop = await db.get(CustomerProperty, quotation.property_id)
    windows: list[dict] = []
    if enquiry.intention == READY_TO_BOOK:
        windows = await suggest_unconfirmed_windows(
            db,
            latitude=float(prop.latitude) if prop and prop.latitude is not None else None,
            longitude=float(prop.longitude) if prop and prop.longitude is not None else None,
            two_stage=two_stage,
        )
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
    if not enquiry.telegram_notified:
        phone = getattr(body, "phone", None) or ""
        summary = f"{body.full_name} · {body.postcode} · {phone}".strip()
        enquiry.telegram_notified = await notify_owner(
            db,
            enquiry,
            reference=quotation.reference if quotation else "",
            summary=summary,
        )
    await db.commit()
    await db.refresh(enquiry)
    return windows


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
    if intention in {READY_TO_BOOK, CALLBACK_REQUESTED} and len(digits) < 8:
        raise HTTPException(status_code=400, detail="Please enter a telephone number.")
    preferred = (getattr(body, "callback_preferred_time", None) or "").strip()
    if intention == CALLBACK_REQUESTED and len(preferred) < 2:
        raise HTTPException(status_code=400, detail="Please tell us when to call.")
