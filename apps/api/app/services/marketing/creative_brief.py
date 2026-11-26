"""Weekly creative brief for external ChatGPT workflow — grounded in real data only."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import MarketingOrganicPost
from app.services.marketing.organic_boost_recommender import recommend_organic_boosts


async def build_weekly_creative_brief(db: AsyncSession) -> dict:
    since = datetime.now(UTC) - timedelta(days=14)
    posts = (
        await db.execute(
            select(MarketingOrganicPost)
            .where(MarketingOrganicPost.published_at >= since)
            .order_by(MarketingOrganicPost.published_at.desc())
        )
    ).scalars().all()
    angle_counts: dict[str, int] = {}
    for p in posts:
        for a in (p.ai_analysis_json or {}).get("angles") or []:
            angle_counts[a] = angle_counts.get(a, 0) + 1
    boosts = await recommend_organic_boosts(db, limit=3)
    under = [p for p in posts if (p.ai_analysis_json or {}).get("angles") == []][:3]
    brief_text = _format_brief_for_chatgpt(posts, angle_counts, boosts, under)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "posts_analysed": len(posts),
        "angle_counts": angle_counts,
        "top_boost_candidates": boosts,
        "underperforming_no_angle": [
            {"permalink": p.permalink, "caption_preview": (p.caption or "")[:100]} for p in under
        ],
        "copy_for_chatgpt": brief_text,
        "disclaimer": "Based on imported organic posts only — not fabricated ad metrics.",
    }


def _format_brief_for_chatgpt(posts, angle_counts, boosts, under) -> str:
    lines = [
        "SurfaceCoat Ltd — weekly creative brief (paste into ChatGPT)",
        "",
        "Brand: charcoal black #1a1a1a, golden yellow #eab308, white. Preston, Lancashire.",
        "Services: tarmac restoration, block paving restoration, commercial surfaces.",
        "Offer framing: restoration vs full replacement. Primary CTA: free quote.",
        "",
        "Angles seen in last 14 days:",
    ]
    for k, v in sorted(angle_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v} posts")
    lines.append("")
    lines.append("Best organic candidates for paid tests:")
    for b in boosts:
        lines.append(f"- {b['platform']}: score {b['engagement_score']} — {b['recommendation']}")
    lines.append("")
    lines.append("Suggested new poster tests (hypotheses):")
    lines.extend(
        [
            "1. Before/after tarmac driveway — headline emphasise restoration not replacement",
            "2. Block paving revival — close-up texture",
            "3. Commercial car park strip — B2B trust cues",
        ]
    )
    lines.append("")
    lines.append("Caption tone: plain English, no guarantees, mark illustrations clearly.")
    lines.append(f"Posts in library: {len(posts)}")
    return "\n".join(lines)