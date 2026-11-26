"""Content calendar views — scheduled items from DB."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import MarketingContentItem


async def calendar_view(db: AsyncSession, *, days: int = 30) -> dict:
    start = datetime.now(UTC) - timedelta(days=1)
    end = start + timedelta(days=days)
    rows = (
        await db.execute(
            select(MarketingContentItem)
            .where(
                (MarketingContentItem.scheduled_for >= start) | (MarketingContentItem.scheduled_for.is_(None))
            )
            .order_by(MarketingContentItem.scheduled_for.nulls_last(), MarketingContentItem.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    by_day: dict[str, list] = {}
    unscheduled = []
    for r in rows:
        entry = {
            "id": str(r.id),
            "platform": r.platform.value,
            "title": r.title,
            "status": r.status.value,
            "scheduled_for": r.scheduled_for.isoformat() if r.scheduled_for else None,
        }
        if r.scheduled_for and r.scheduled_for <= end:
            day = r.scheduled_for.date().isoformat()
            by_day.setdefault(day, []).append(entry)
        else:
            unscheduled.append(entry)
    return {"days": by_day, "unscheduled_drafts": unscheduled[:20], "window_days": days}