"""Link Telegram marketing photos to jobs by reference."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Job
from app.models.marketing_ops import MarketingJobMediaStaging, MarketingMediaAsset
from app.services.marketing.before_after import build_before_after_package

JOB_REF_RE = re.compile(r"\b(RMD-[A-Z0-9]{4,})\b", re.I)


def parse_job_reference(caption: str) -> str | None:
    m = JOB_REF_RE.search(caption.upper().replace(" ", ""))
    if m:
        return m.group(1).upper()
    m2 = JOB_REF_RE.search(caption.upper())
    return m2.group(1).upper() if m2 else None


async def stage_telegram_photo(
    db: AsyncSession,
    *,
    asset: MarketingMediaAsset,
    caption: str,
    phase: str,
) -> dict:
    ref = parse_job_reference(caption)
    job = None
    if ref:
        job = (await db.execute(select(Job).where(Job.reference == ref))).scalar_one_or_none()
    db.add(
        MarketingJobMediaStaging(
            job_id=job.id if job else None,
            job_reference=ref,
            asset_id=asset.id,
            phase=phase,
        )
    )
    if job:
        asset.job_id = job.id
    await db.flush()
    paired = None
    if job and phase == "after":
        before_row = (
            await db.execute(
                select(MarketingJobMediaStaging)
                .where(
                    MarketingJobMediaStaging.job_id == job.id,
                    MarketingJobMediaStaging.phase == "before",
                )
                .order_by(MarketingJobMediaStaging.created_at.desc())
            )
        ).scalar_one_or_none()
        if before_row:
            permission = "permission" in caption.lower() and asset.customer_permission
            paired = await build_before_after_package(
                db,
                job_id=job.id,
                before_asset_id=before_row.asset_id,
                after_asset_id=asset.id,
                customer_permission=permission,
            )
    return {
        "job_reference": ref,
        "job_found": job is not None,
        "phase": phase,
        "before_after_package": paired,
    }