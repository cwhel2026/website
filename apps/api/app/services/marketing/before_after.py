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
from app.services.marketing.image_compositor import FORMATS, render_before_after
from app.services.marketing.media_store import store_bytes
from app.models.marketing_ops import MarketingRenderedCreative


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
    from sqlalchemy import select

    before_asset = (
        await db.execute(select(MarketingMediaAsset).where(MarketingMediaAsset.id == before_asset_id))
    ).scalar_one_or_none()
    after_asset = (
        await db.execute(select(MarketingMediaAsset).where(MarketingMediaAsset.id == after_asset_id))
    ).scalar_one_or_none()
    if not before_asset or not after_asset:
        return {"ok": False, "message": "Before/after assets not found"}
    package = MarketingBeforeAfterPackage(
        job_id=job_id,
        before_asset_id=before_asset_id,
        after_asset_id=after_asset_id,
        customer_permission=customer_permission,
        layout_status="rendering",
    )
    db.add(package)
    await db.flush()
    renders: list[dict] = []
    for fmt in FORMATS:
        try:
            key, _ = render_before_after(
                before_key=before_asset.storage_key,
                after_key=after_asset.storage_key,
                format_name=fmt,
            )
            w, h = FORMATS[fmt]
            creative = MarketingRenderedCreative(
                package_id=package.id, format=fmt, storage_key=key, width=w, height=h
            )
            db.add(creative)
            renders.append({"format": fmt, "storage_key": key})
        except Exception as exc:
            renders.append({"format": fmt, "error": str(exc)[:120]})
    package.layout_status = "pending_approval"
    item = await generate_platform_content(
        db,
        platform=ContentPlatform.FACEBOOK,
        brief="Before-and-after driveway restoration (genuine completed work)",
    )
    package.content_item_id = item.id
    await db.flush()
    return {
        "ok": True,
        "package_id": str(package.id),
        "content_item_id": str(item.id),
        "renders": renders,
    }

