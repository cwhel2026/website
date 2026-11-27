"""Attach driveway photographs to the customer, property, enquiry and quotation."""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quotation import Quotation
from app.models.quotation_photo import QuotePhoto, QuotePhotoSet
from app.services.quote_photo_ai import (
    SIGNIFICANT,
    assess_image_bytes,
    customer_summary,
    failed_assessment,
)
from app.services.quote_photo_store import (
    MAX_PHOTOS,
    delete_photo_file,
    prepare_image,
    read_photo_bytes,
    save_photo_bytes,
)

logger = logging.getLogger(__name__)
RETENTION_DAYS = 730


def new_photo_set() -> QuotePhotoSet:
    return QuotePhotoSet(
        token=secrets.token_urlsafe(32),
        marketing_use_allowed=False,
        ai_status="pending",
        review_required=False,
        review_status="not_required",
        retain_until=datetime.now(UTC) + timedelta(days=RETENTION_DAYS),
    )


async def load_set(db: AsyncSession, token: str) -> QuotePhotoSet:
    if not token or len(token) > 80:
        raise HTTPException(status_code=404, detail="Photograph link was not recognised")
    row = await db.scalar(
        select(QuotePhotoSet).options(selectinload(QuotePhotoSet.photos)).where(QuotePhotoSet.token == token)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Photograph link was not recognised")
    return row


async def add_photos(
    db: AsyncSession,
    photo_set: QuotePhotoSet,
    blobs: list[bytes],
    *,
    note: str | None,
    replace_id: UUID | None,
) -> QuotePhotoSet:
    if replace_id is not None:
        await remove_photo(db, photo_set, replace_id)
    if not blobs:
        raise HTTPException(status_code=400, detail="Choose a photograph to upload")
    if len(photo_set.photos) + len(blobs) > MAX_PHOTOS:
        raise HTTPException(status_code=400, detail=f"You can add up to {MAX_PHOTOS} photographs")
    prepared: list[bytes] = []
    for raw in blobs:
        try:
            prepared.append(prepare_image(raw))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    for jpeg in prepared:
        key, digest = save_photo_bytes(jpeg)
        photo_set.photos.append(
            QuotePhoto(storage_key=key, sha256=digest, byte_size=len(jpeg))
        )
    if note is not None and note.strip():
        photo_set.customer_note = note.strip()[:1000]
    photo_set.ai_status = "pending"
    photo_set.marketing_use_allowed = False
    return photo_set


async def remove_photo(db: AsyncSession, photo_set: QuotePhotoSet, photo_id: UUID) -> None:
    match = next((photo for photo in photo_set.photos if photo.id == photo_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Photograph not found")
    delete_photo_file(match.storage_key)
    photo_set.photos.remove(match)
    await db.delete(match)


async def link_photo_set(
    db: AsyncSession,
    *,
    token: str | None,
    quotation_id: UUID,
    enquiry_id: UUID | None,
    customer_id: UUID | None,
    property_id: UUID | None,
    note: str | None,
) -> str:
    existing = await db.scalar(select(QuotePhotoSet).where(QuotePhotoSet.quotation_id == quotation_id))
    row: QuotePhotoSet | None = None
    cleaned = (token or "").strip()
    if cleaned:
        row = await db.scalar(select(QuotePhotoSet).where(QuotePhotoSet.token == cleaned))
        if row is None:
            raise HTTPException(status_code=400, detail="Photograph link was not recognised")
        if row.quotation_id is not None and row.quotation_id != quotation_id:
            raise HTTPException(status_code=409, detail="These photographs are already attached to another quotation")
    if existing is not None and (row is None or existing.id != row.id):
        return existing.token
    if row is None:
        row = new_photo_set()
        db.add(row)
    row.quotation_id = quotation_id
    row.enquiry_id = enquiry_id
    row.customer_id = customer_id
    row.property_id = property_id
    row.marketing_use_allowed = False
    if note and note.strip():
        row.customer_note = note.strip()[:1000]
    return row.token


def record_repair_decision(
    photo_set: QuotePhotoSet,
    *,
    repair_price_gbp: Decimal | None,
    repair_note: str,
    approved: bool,
) -> None:
    """Record an owner decision. Callers must not copy this price onto the quotation."""
    photo_set.repair_price_gbp = repair_price_gbp
    photo_set.repair_note = repair_note.strip()[:500]
    photo_set.review_status = "approved" if approved else "open"


async def photo_counts_for_quotations(db: AsyncSession, quotation_ids: list[UUID]) -> dict[UUID, int]:
    if not quotation_ids:
        return {}
    rows = await db.execute(
        select(QuotePhotoSet.quotation_id, func.count(QuotePhoto.id))
        .join(QuotePhoto, QuotePhoto.set_id == QuotePhotoSet.id)
        .where(QuotePhotoSet.quotation_id.in_(quotation_ids))
        .group_by(QuotePhotoSet.quotation_id)
    )
    return {quotation_id: int(count) for quotation_id, count in rows.all() if quotation_id is not None}


async def purge_expired_quote_photos(db: AsyncSession) -> int:
    now = datetime.now(UTC)
    sets = (
        await db.scalars(
            select(QuotePhotoSet).options(selectinload(QuotePhotoSet.photos)).where(QuotePhotoSet.retain_until < now)
        )
    ).all()
    removed = 0
    for photo_set in sets:
        for photo in list(photo_set.photos):
            delete_photo_file(photo.storage_key)
            removed += 1
        await db.delete(photo_set)
    return removed


async def assess_photo_set(set_id: UUID) -> None:
    """Background assessment. Failures stay on the photograph row and do not touch the price."""
    from app.database import SessionLocal
    from app.services.ai.usage_limits import check_spend_allowed, estimate_openai_cost_gbp, record_usage

    try:
        async with SessionLocal() as db:
            photo_set = await db.scalar(
                select(QuotePhotoSet).options(selectinload(QuotePhotoSet.photos)).where(QuotePhotoSet.id == set_id)
            )
            if photo_set is None or not photo_set.photos:
                return
            allowed, _reason = await check_spend_allowed(db)
            findings: list[dict] = []
            statuses: list[str] = []
            prompt_tokens = 0
            completion_tokens = 0
            for photo in photo_set.photos:
                if not allowed:
                    result = failed_assessment()
                    result["status"] = "unavailable"
                    result["summary"] = (
                        "Photograph saved. Automatic assessment is paused, so the estimate is unchanged."
                    )
                else:
                    try:
                        result = await assess_image_bytes(read_photo_bytes(photo.storage_key))
                    except Exception:
                        logger.exception("could not read driveway photograph")
                        result = failed_assessment()
                statuses.append(result["status"])
                prompt_tokens += int(result.get("prompt_tokens") or 0)
                completion_tokens += int(result.get("completion_tokens") or 0)
                for item in result["findings"]:
                    findings.append({"photo_id": str(photo.id), "kind": item["kind"], "note": item["note"]})
            review = any(item["kind"] in SIGNIFICANT for item in findings)
            photo_set.findings_json = findings
            photo_set.review_required = review
            if review:
                photo_set.review_status = "open"
            elif photo_set.review_status != "approved":
                photo_set.review_status = "not_required"
            if statuses and all(status == "unavailable" for status in statuses):
                photo_set.ai_status = "unavailable"
            elif any(status == "assessed" for status in statuses):
                photo_set.ai_status = "assessed"
            else:
                photo_set.ai_status = "failed"
            photo_set.ai_summary = customer_summary(findings, review)
            if prompt_tokens or completion_tokens:
                settings_model = "gpt-4o-mini"
                from app.config import get_settings

                settings_model = get_settings().openai_model
                await record_usage(
                    db,
                    provider="openai",
                    model=settings_model,
                    agent_slug="quote-photos",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    estimated_cost_gbp=estimate_openai_cost_gbp(prompt_tokens, completion_tokens, settings_model),
                )
            quotation_total = None
            if photo_set.quotation_id:
                quotation_total = await db.scalar(
                    select(Quotation.total_inc_vat_gbp).where(Quotation.id == photo_set.quotation_id)
                )
            await db.commit()
            if quotation_total is not None:
                logger.info("photo assessment left quotation total at %s", quotation_total)
    except Exception:
        logger.exception("driveway photograph assessment failed")
        try:
            async with SessionLocal() as db:
                photo_set = await db.get(QuotePhotoSet, set_id)
                if photo_set is not None and photo_set.ai_status == "pending":
                    photo_set.ai_status = "failed"
                    photo_set.ai_summary = failed_assessment()["summary"]
                    await db.commit()
        except Exception:
            logger.exception("could not record driveway photograph assessment failure")
