"""Before/after workflow — associate Telegram uploads with jobs and queue content."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import (
    ContentPlatform,
    MarketingBeforeAfterPackage,
    MarketingMediaAsset,
)
from app.services.marketing.content_studio import generate_platform_content
from app.services.marketing.media_store import store_bytes


async def ingest_marketing_photo(
    db: AsyncSession,
    *,
    data: bytes,
    filename: str,
    job_id: uuid.UUID | None,
    telegram_file_id: str | None,
    is_before: bool,
    customer_permission: bool,
) -> MarketingMediaAsset:
    key, digest = store_bytes(data=data, filename=filename, subdir="jobs")
    asset = MarketingMediaAsset(
        storage_key=key,
        filename=filename,
        content_sha256=digest,
        job_id=job_id,
        source="telegram",
        telegram_file_id=telegram_file_id,
        customer_permission=customer_permission,
        category="before" if is_before else "after",
    )
    db.add(asset)
    await db.flush()
    return asset


async def build_before_after_package(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    before_asset_id: uuid.UUID,
    after_asset_id: uuid.UUID,
    customer_permission: bool,
) -> dict:
    if not customer_permission:
        return {"ok": False, "message": "Customer permission required for before/after marketing"}
    package = MarketingBeforeAfterPackage(
        job_id=job_id,
        before_asset_id=before_asset_id,
        after_asset_id=after_asset_id,
        customer_permission=customer_permission,
        layout_status="captions_ready",
    )
    item = await generate_platform_content(
        db,
        platform=ContentPlatform.FACEBOOK,
        brief="Before-and-after driveway restoration (genuine completed work)",
    )
    package.content_item_id = item.id
    db.add(package)
    await db.flush()
    return {
        "ok": True,
        "package_id": str(package.id),
        "content_item_id": str(item.id),
        "note": "Branded layout renderer pending — captions queued for approval",
    }