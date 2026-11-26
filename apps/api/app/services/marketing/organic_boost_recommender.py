"""Recommend organic posts for paid boost — approval required, no auto-launch."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import MarketingOrganicPost


def _engagement_score(post: MarketingOrganicPost) -> float:
    m = post.metrics_json or {}
    likes = float(m.get("likes") or 0)
    shares = float((m.get("shares") or {}).get("count") if isinstance(m.get("shares"), dict) else m.get("shares") or 0)
    comments = float(m.get("comments") or 0)
    ig = m.get("instagram_insights") or {}
    reach_hint = 1.0
    for _k, vals in ig.items():
        if isinstance(vals, list) and vals:
            reach_hint = max(reach_hint, float(vals[0].get("value", 1) if isinstance(vals[0], dict) else 1))
    raw = likes * 1 + comments * 2 + shares * 3
    return raw / reach_hint


async def recommend_organic_boosts(db: AsyncSession, *, limit: int = 5) -> list[dict]:
    rows = (
        await db.execute(
            select(MarketingOrganicPost).order_by(MarketingOrganicPost.published_at.desc().nullslast()).limit(40)
        )
    ).scalars().all()
    scored = []
    for p in rows:
        score = _engagement_score(p)
        angles = (p.ai_analysis_json or {}).get("angles") or []
        scored.append(
            {
                "post_id": str(p.id),
                "platform": p.platform.value,
                "permalink": p.permalink,
                "caption_preview": (p.caption or "")[:160],
                "engagement_score": round(score, 2),
                "angles": angles,
                "confidence": "low" if score < 2 else ("medium" if score < 8 else "high"),
                "recommendation": _recommendation_text(p, score),
                "proposed_action": "boost_existing_post",
                "requires_approval": True,
                "certainty": "estimate",
            }
        )
    scored.sort(key=lambda x: x["engagement_score"], reverse=True)
    return scored[:limit]


def _recommendation_text(post: MarketingOrganicPost, score: float) -> str:
    risks = (post.ai_analysis_json or {}).get("misleading_risk") or []
    if risks:
        return f"Review claims ({', '.join(risks)}) before promoting."
    if score < 2:
        return "Low signal — wait for more reach or engagement data."
    if "before_after" in ((post.ai_analysis_json or {}).get("angles") or []):
        return "Strong transformation creative — test as lead ad using existing post ID if objective allows."
    return "Consider a small boost to a consolidated lead campaign (£150/week cap)."