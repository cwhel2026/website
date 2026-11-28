"""UK GDPR / PECR safeguards for B2B outreach drafts — no external send without approval."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import CommercialProspect, OutreachMessage, OutreachMessageStatus


def validate_outreach_eligibility(prospect: CommercialProspect) -> tuple[bool, str]:
    if prospect.opt_out:
        return False, "Prospect has opted out."
    if not prospect.contact_email or prospect.is_corporate_subscriber is not True:
        return False, "Verified corporate subscriber and contact email required."
    if not prospect.lawful_basis:
        return False, "Lawful basis not recorded."
    return True, "OK"


def build_introduction_email(prospect: CommercialProspect) -> tuple[str, str]:
    subject = f"Surface restoration survey — {prospect.business_name}"
    body = (
        f"Dear {prospect.contact_name or 'Facilities team'},\n\n"
        f"I am writing from SurfaceCoat Ltd regarding the car park and external surfaces "
        f"at {prospect.site_address or 'your premises'}.\n\n"
        "We specialise in tarmac and block paving restoration, pressure washing and line marking "
        "across Lancashire, Merseyside and Greater Manchester — often avoiding full resurfacing "
        "where restoration is suitable.\n\n"
        "If you are responsible for maintenance, I would be glad to arrange a no-obligation site "
        "walk-around at a convenient time.\n\n"
        "SurfaceCoat Ltd\n"
        "Unsubscribe: reply STOP\n"
    )
    return subject, body


async def create_outreach_draft(
    db: AsyncSession, prospect: CommercialProspect
) -> tuple[OutreachMessage | None, str]:
    await db.refresh(prospect, with_for_update=True)
    ok, reason = validate_outreach_eligibility(prospect)
    if not ok:
        return None, reason
    existing = await db.scalar(select(OutreachMessage).where(OutreachMessage.prospect_id == prospect.id, OutreachMessage.status.in_([OutreachMessageStatus.DRAFT, OutreachMessageStatus.PENDING_APPROVAL, OutreachMessageStatus.APPROVED, OutreachMessageStatus.SENT])).limit(1))
    if existing:
        return existing, "Existing outreach record; no duplicate draft created."
    subject, body = build_introduction_email(prospect)
    msg = OutreachMessage(
        prospect_id=prospect.id,
        subject=subject,
        body_text=body,
        status=OutreachMessageStatus.PENDING_APPROVAL,
    )
    db.add(msg)
    await db.flush()
    return msg, "Draft created — owner approval required before any send."