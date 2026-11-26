"""Import Facebook / Instagram organic posts — idempotent, with metric snapshots."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import MarketingOrganicPost, MarketingOrganicPostSnapshot, OrganicPlatform
from app.services.marketing.meta_graph_client import (
    fetch_instagram_media,
    fetch_page_posts,
    fetch_post_insights,
)
from app.services.marketing.organic_post_analysis import analyse_organic_caption


def _parse_fb_time(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _upsert_post(
    db: AsyncSession,
    *,
    platform: OrganicPlatform,
    external_id: str,
    caption: str | None,
    published_at: datetime | None,
    permalink: str | None,
    media_refs: list | dict | None,
    fmt: str | None,
    raw: dict,
    metrics: dict | None,
) -> tuple[MarketingOrganicPost, bool]:
    row = (
        await db.execute(
            select(MarketingOrganicPost).where(
                MarketingOrganicPost.platform == platform,
                MarketingOrganicPost.external_post_id == external_id,
            )
        )
    ).scalar_one_or_none()
    created = row is None
    if row is None:
        row = MarketingOrganicPost(
            platform=platform,
            external_post_id=external_id,
        )
        db.add(row)
    row.caption = caption
    row.published_at = published_at
    row.permalink = permalink
    row.media_refs_json = media_refs
    row.format = fmt
    row.raw_payload_json = raw
    row.ai_analysis_json = analyse_organic_caption(caption)
    row.last_synced_at = datetime.now(UTC)
    await db.flush()
    if metrics:
        prev = dict(row.metrics_json or {})
        prev.update(metrics)
        row.metrics_json = prev
        db.add(
            MarketingOrganicPostSnapshot(post_id=row.id, metrics_json=metrics)
        )
    if created and row.id:
        pass
    return row, created


async def sync_facebook_posts(db: AsyncSession, *, limit: int = 25) -> dict[str, Any]:
    pulled = await fetch_page_posts(limit=limit)
    if not pulled.get("ok"):
        return {"ok": False, "platform": "facebook", "message": pulled.get("message"), "imported": 0}
    imported = 0
    for p in pulled.get("posts") or []:
        ext = p.get("id")
        if not ext:
            continue
        ins = await fetch_post_insights("facebook", ext)
        metrics = ins.get("metrics") if ins.get("ok") else {}
        media = []
        if p.get("full_picture"):
            media.append({"type": "image", "url": p.get("full_picture")})
        row, created = await _upsert_post(
            db,
            platform=OrganicPlatform.FACEBOOK,
            external_id=ext,
            caption=p.get("message"),
            published_at=_parse_fb_time(p.get("created_time")),
            permalink=p.get("permalink_url"),
            media_refs=media,
            fmt="photo",
            raw=p,
            metrics={"facebook_insights": metrics, "shares": p.get("shares")},
        )
        if created:
            imported += 1
        await db.refresh(row)
    return {"ok": True, "platform": "facebook", "imported": imported, "seen": len(pulled.get("posts") or [])}


async def sync_instagram_posts(db: AsyncSession, *, limit: int = 25) -> dict[str, Any]:
    pulled = await fetch_instagram_media(limit=limit)
    if not pulled.get("ok"):
        return {"ok": False, "platform": "instagram", "message": pulled.get("message"), "imported": 0}
    imported = 0
    for p in pulled.get("posts") or []:
        ext = p.get("id")
        if not ext:
            continue
        ins = await fetch_post_insights("instagram", ext)
        metrics = ins.get("metrics") if ins.get("ok") else {}
        metrics["likes"] = p.get("like_count")
        metrics["comments"] = p.get("comments_count")
        media = [{"type": p.get("media_type"), "url": p.get("media_url")}] if p.get("media_url") else []
        row, created = await _upsert_post(
            db,
            platform=OrganicPlatform.INSTAGRAM,
            external_id=ext,
            caption=p.get("caption"),
            published_at=_parse_fb_time(p.get("timestamp")),
            permalink=p.get("permalink"),
            media_refs=media,
            fmt=(p.get("media_type") or "media").lower(),
            raw=p,
            metrics={"instagram_insights": metrics},
        )
        if created:
            imported += 1
        await db.refresh(row)
    return {"ok": True, "platform": "instagram", "imported": imported, "seen": len(pulled.get("posts") or [])}


async def sync_all_organic(db: AsyncSession) -> dict:
    fb = await sync_facebook_posts(db)
    ig = await sync_instagram_posts(db)
    return {"facebook": fb, "instagram": ig, "synced_at": datetime.now(UTC).isoformat()}