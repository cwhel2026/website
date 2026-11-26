"""Competitor intelligence from permitted APIs only — no invented data."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import CompetitorIntelligenceFinding
from app.services.marketing.research.google_places import search_places


async def research_competitors(
    db: AsyncSession,
    *,
    area: str,
    territory_code: str | None = None,
) -> dict:
    queries = [
        f"driveway cleaning {area}",
        f"tarmac restoration {area}",
        f"block paving cleaning {area}",
    ]
    imported = 0
    for q in queries:
        result = await search_places(query=q)
        if not result.get("ok"):
            continue
        for item in result.get("items") or []:
            name = item.get("name")
            if not name:
                continue
            exists = await db.execute(
                select(CompetitorIntelligenceFinding).where(
                    CompetitorIntelligenceFinding.competitor_name == name,
                    CompetitorIntelligenceFinding.finding_type == "places_listing",
                )
            )
            if exists.scalar_one_or_none():
                continue
            types = ", ".join(item.get("types") or [])
            summary = f"Public listing: {types}. Address: {item.get('address') or 'not returned by API'}."
            db.add(
                CompetitorIntelligenceFinding(
                    competitor_name=name[:255],
                    territory_code=territory_code,
                    category="driveway_restoration",
                    finding_type="places_listing",
                    summary=summary,
                    source_name=item.get("source", "Google Places API"),
                    source_url=item.get("source_url"),
                    confidence=70,
                    retrieved_at=datetime.now(UTC),
                    payload_json={**item, "pricing": None, "note": "Pricing not available from Places without verified source"},
                )
            )
            imported += 1
    await db.flush()
    return {
        "ok": True,
        "imported": imported,
        "queries_run": queries,
        "disclaimer": "Only API-returned fields stored. Reviews/prices require separate verified sources.",
    }


async def list_competitor_findings(db: AsyncSession, limit: int = 50) -> list[dict]:
    rows = (
        await db.execute(
            select(CompetitorIntelligenceFinding).order_by(CompetitorIntelligenceFinding.retrieved_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "competitor_name": r.competitor_name,
            "territory_code": r.territory_code,
            "summary": r.summary,
            "source_name": r.source_name,
            "source_url": r.source_url,
            "confidence": r.confidence,
            "retrieved_at": r.retrieved_at.isoformat(),
        }
        for r in rows
    ]