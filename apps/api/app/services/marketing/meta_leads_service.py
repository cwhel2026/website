"""Meta leadgen webhook ingestion with dedupe."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Customer, Enquiry, PipelineStage
from app.models.marketing import AttributionEvent
from app.models.marketing_ops import MarketingMetaLead


def _dedupe(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)[:2000]
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def ingest_meta_lead_payload(db: AsyncSession, payload: dict) -> dict:
    dedupe = _dedupe(payload)
    existing = await db.execute(select(MarketingMetaLead).where(MarketingMetaLead.dedupe_key == dedupe))
    if existing.scalar_one_or_none():
        return {"ok": True, "duplicate": True}
    leadgen_id = str(payload.get("leadgen_id") or payload.get("id") or dedupe)
    if (await db.execute(select(MarketingMetaLead).where(MarketingMetaLead.leadgen_id == leadgen_id))).scalar_one_or_none():
        return {"ok": True, "duplicate": True}
    placeholder_email = f"meta-lead-{leadgen_id[:16]}@leads.invalid"
    customer = Customer(full_name="Meta lead", email=placeholder_email, phone=None, source="meta_leadgen")
    db.add(customer)
    await db.flush()
    enquiry = Enquiry(customer_id=customer.id, message="Meta lead form submission", stage=PipelineStage.NEW_ENQUIRY)
    db.add(enquiry)
    await db.flush()
    db.add(
        AttributionEvent(
            source="meta",
            medium="paid_social",
            utm_source="meta",
            content="leadgen",
            customer_id=customer.id,
            enquiry_id=enquiry.id,
        )
    )
    lead_row = MarketingMetaLead(
        leadgen_id=leadgen_id,
        enquiry_id=enquiry.id,
        payload_json=payload,
        dedupe_key=dedupe,
    )
    db.add(lead_row)
    await db.flush()
    return {"ok": True, "enquiry_id": str(enquiry.id), "duplicate": False}