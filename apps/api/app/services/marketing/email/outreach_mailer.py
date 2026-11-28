"""Outbound business email — disabled unless policy + SMTP configured + message approved."""

from __future__ import annotations

import asyncio
import re
import smtplib
import uuid
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.marketing_ops import (
    MarketingEmailSuppression,
    OutreachMessage,
    OutreachMessageStatus,
)
from app.services.marketing.budget_controls import get_or_create_budget_policy
from app.services.marketing.outreach_compliance import validate_outreach_eligibility


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def is_suppressed(db: AsyncSession, email: str) -> bool:
    norm = _normalize_email(email)
    row = await db.execute(
        select(MarketingEmailSuppression).where(MarketingEmailSuppression.email_normalized == norm)
    )
    return row.scalar_one_or_none() is not None


async def suppress_email(db: AsyncSession, email: str, reason: str) -> None:
    norm = _normalize_email(email)
    existing = await db.execute(
        select(MarketingEmailSuppression).where(MarketingEmailSuppression.email_normalized == norm)
    )
    if existing.scalar_one_or_none():
        return
    db.add(MarketingEmailSuppression(email_normalized=norm, reason=reason))


async def sent_count_today(db: AsyncSession) -> int:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        await db.scalar(
            select(func.count())
            .select_from(OutreachMessage)
            .where(OutreachMessage.status == OutreachMessageStatus.SENT, OutreachMessage.sent_at >= start)
        )
        or 0
    )


def _smtp_send(msg: EmailMessage) -> str:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        raise RuntimeError("SMTP not configured")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return f"smtp-{uuid.uuid4().hex[:12]}"


async def send_approved_outreach(db: AsyncSession, message: OutreachMessage, *, to_email: str) -> dict:
    policy = await get_or_create_budget_policy(db)
    await db.refresh(policy, with_for_update=True)
    if message.status != OutreachMessageStatus.APPROVED:
        return {"ok": False, "message": "Explicit approval required"}
    if policy.emergency_pause_all or not policy.outreach_email_enabled:
        return {"ok": False, "message": "Outreach email disabled in budget policy"}
    if await is_suppressed(db, to_email):
        message.status = OutreachMessageStatus.SUPPRESSED
        message.delivery_status = "suppressed"
        return {"ok": False, "message": "Recipient on suppression list"}
    if await sent_count_today(db) >= policy.outreach_daily_cap:
        return {"ok": False, "message": "Daily outreach cap reached"}

    settings = get_settings()
    em = EmailMessage()
    em["Subject"] = message.subject
    em["From"] = f"{settings.outreach_from_name} <{settings.outreach_from_email}>"
    em["To"] = to_email
    em["List-Unsubscribe"] = f"<mailto:{settings.outreach_from_email}?subject=unsubscribe>"
    body = message.body_text
    if "unsubscribe" not in body.lower():
        body += f"\n\nReply STOP to opt out. {settings.outreach_from_name}."
    em.set_content(body)

    if not (settings.smtp_host and settings.smtp_user and settings.smtp_password):
        message.delivery_status = "not_sent_smtp_unconfigured"
        return {
            "ok": False,
            "live": False,
            "message": "Not sent: SMTP is not configured. The message remains approved and unsent.",
        }

    try:
        provider_id = await asyncio.to_thread(_smtp_send, em)
        message.status = OutreachMessageStatus.SENT
        message.sent_at = datetime.now(UTC)
        message.provider_message_id = provider_id
        message.delivery_status = "sent"
        return {"ok": True, "provider_message_id": provider_id, "live": True}
    except Exception as exc:
        message.status = OutreachMessageStatus.FAILED
        message.delivery_status = "failed"
        return {"ok": False, "message": "SMTP delivery failed; verify delivery before retrying"}


async def approve_and_send(
    db: AsyncSession, message: OutreachMessage, prospect
) -> dict:
    ok, reason = validate_outreach_eligibility(prospect)
    if not ok:
        return {"ok": False, "message": reason}
    if message.status != OutreachMessageStatus.APPROVED:
        return {"ok": False, "message": "Message not approved"}
    if not prospect.contact_email:
        return {"ok": False, "message": "No verified contact email — cannot send"}
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", prospect.contact_email):
        return {"ok": False, "message": "Invalid email format"}
    return {"ok": False, "live": False, "message": "External sending deferred until sender and delivery idempotency are verified"}


async def record_reply(db: AsyncSession, *, email: str) -> int:
    """Cancel follow-ups when recipient replies."""
    norm = _normalize_email(email)
    from app.models.marketing_ops import CommercialProspect

    pros = (
        await db.execute(select(CommercialProspect).where(CommercialProspect.contact_email.ilike(norm)))
    ).scalars().all()
    count = 0
    for p in pros:
        msgs = (
            await db.execute(
                select(OutreachMessage).where(
                    OutreachMessage.prospect_id == p.id,
                    OutreachMessage.status.in_(
                        (OutreachMessageStatus.SENT, OutreachMessageStatus.APPROVED, OutreachMessageStatus.PENDING_APPROVAL)
                    ),
                )
            )
        ).scalars().all()
        for m in msgs:
            m.status = OutreachMessageStatus.REPLIED
            m.replied_at = datetime.now(UTC)
            count += 1
    return count