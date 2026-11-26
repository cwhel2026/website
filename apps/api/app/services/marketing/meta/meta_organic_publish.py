"""Meta Page feed publish — pre-launch dry-run when tokens missing."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.marketing_ops import MarketingContentItem, MarketingPublicationLog


async def publish_content_item(db: AsyncSession, item: MarketingContentItem, *, force_simulation: bool | None = None) -> dict:
    key = item.idempotency_key or hashlib.sha256(f"{item.id}-{item.updated_at if hasattr(item,'updated_at') else ''}".encode()).hexdigest()[:32]
    item.idempotency_key = key
    from sqlalchemy import select

    existing = await db.execute(select(MarketingPublicationLog).where(MarketingPublicationLog.idempotency_key == key))
    if existing.scalar_one_or_none():
        return {"ok": True, "duplicate_prevented": True, "idempotency_key": key}

    settings = get_settings()
    simulate = force_simulation if force_simulation is not None else not (settings.meta_access_token and settings.meta_page_id)
    log = MarketingPublicationLog(
        content_item_id=item.id,
        platform=item.platform.value,
        idempotency_key=key,
        status="simulated" if simulate else "pending",
        simulated=simulate,
    )
    if simulate:
        log.status = "simulated"
        log.external_id = f"sim-{uuid.uuid4().hex[:10]}"
        log.published_at = datetime.now(UTC)
        db.add(log)
        await db.flush()
        return {
            "ok": True,
            "simulated": True,
            "message": "Pre-launch: connect META_PAGE_ID and token for live publish",
            "external_id": log.external_id,
        }

    page_id = settings.meta_page_id
    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                url,
                data={"message": item.body_text[:63206], "access_token": settings.meta_access_token},
            )
            payload = resp.json()
            if resp.status_code >= 400:
                log.status = "failed"
                log.error = str(payload)[:500]
                db.add(log)
                await db.flush()
                return {"ok": False, "message": log.error}
    except httpx.HTTPError as exc:
        log.status = "failed"
        log.error = str(exc)[:300]
        db.add(log)
        await db.flush()
        return {"ok": False, "message": log.error}
    log.status = "published"
    log.external_id = payload.get("id")
    log.published_at = datetime.now(UTC)
    db.add(log)
    await db.flush()
    return {"ok": True, "simulated": False, "external_id": log.external_id}