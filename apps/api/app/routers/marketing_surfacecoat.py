"""SurfaceCoat Meta marketing director API."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.marketing_ops import MarketingBudgetPolicy, MarketingDirectorMode, MarketingOrganicPost
from app.models.user import User
from app.services.marketing.budget_controls import get_or_create_budget_policy
from app.services.marketing.creative_brief import build_weekly_creative_brief
from app.services.marketing.launch_programme import DEFAULT_LAUNCH_PROGRAMME, ensure_launch_programme
from app.services.marketing.meta_graph_client import account_spend_last_7d
from app.services.marketing.meta_wizard import meta_connection_wizard, run_connection_tests
from app.services.marketing.organic_boost_recommender import recommend_organic_boosts
from app.services.marketing.organic_post_sync import sync_all_organic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketing/surfacecoat", tags=["marketing-surfacecoat"])


@router.get("/overview")
async def overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    degraded: list[str] = []
    policy = await get_or_create_budget_policy(db)
    await ensure_launch_programme(policy)
    await db.commit()

    spend = await account_spend_last_7d()
    meta_spend = float(spend.get("spend_gbp") or 0) if spend.get("ok") else None
    meta_source = "meta_api" if spend.get("ok") else (spend.get("message") or "Meta not connected")

    posts = 0
    try:
        posts = int(await db.scalar(select(func.count()).select_from(MarketingOrganicPost)) or 0)
    except Exception:
        logger.exception("marketing overview: organic post count failed")
        await db.rollback()
        degraded.append("organic_posts_unavailable")

    growth: dict | None = None
    try:
        from app.services.marketing.growth_fund import fund_summary

        growth = await fund_summary(db)
    except Exception:
        logger.exception("marketing overview: growth fund summary failed")
        await db.rollback()
        degraded.append("growth_fund_unavailable")

    return {
        "pre_launch_mode": not policy.live_paid_spend_approved,
        "weekly_budget_gbp": float(policy.weekly_limit_gbp),
        "remaining_budget_estimate_gbp": max(0.0, float(policy.weekly_limit_gbp) - (meta_spend or 0)),
        "meta_account_spend_7d_gbp": meta_spend,
        "meta_spend_source": meta_source,
        "organic_posts_total": posts,
        "director_mode": policy.director_operating_mode.value,
        "emergency_pause": policy.emergency_pause_all,
        "launch_programme": policy.launch_programme_json or DEFAULT_LAUNCH_PROGRAMME,
        "growth_fund": growth,
        "degraded": degraded,
        "disclaimer": "Spend from Meta may lag; campaigns edited in Ads Manager may not appear immediately.",
    }


@router.get("/organic-posts")
async def list_organic_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    limit: int = 50,
) -> list[dict]:
    rows = (
        await db.execute(
            select(MarketingOrganicPost).order_by(MarketingOrganicPost.published_at.desc().nullslast()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "platform": r.platform.value,
            "permalink": r.permalink,
            "caption": r.caption,
            "published_at": r.published_at.isoformat() if r.published_at else None,
            "format": r.format,
            "metrics": r.metrics_json,
            "analysis": r.ai_analysis_json,
        }
        for r in rows
    ]


@router.post("/organic-posts/sync")
async def trigger_organic_sync(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await sync_all_organic(db)
    await db.commit()
    return result


@router.get("/recommendations/organic-boost")
async def organic_boost_recommendations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    items = await recommend_organic_boosts(db)
    return {"requires_approval": True, "items": items}


@router.get("/creative-brief")
async def weekly_creative_brief(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await build_weekly_creative_brief(db)


class LaunchProgrammePatch(BaseModel):
    launch_programme_json: dict | None = None
    director_operating_mode: MarketingDirectorMode | None = None


@router.get("/launch-programme")
async def get_launch_programme(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    programme = await ensure_launch_programme(policy)
    await db.commit()
    return {"programme": programme, "geo": policy.geo_target_json}


@router.patch("/launch-programme")
async def patch_launch_programme(
    body: LaunchProgrammePatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    if body.launch_programme_json is not None:
        policy.launch_programme_json = body.launch_programme_json
    if body.director_operating_mode is not None:
        policy.director_operating_mode = body.director_operating_mode
    await db.commit()
    return {"ok": True}


@router.get("/meta/wizard")
async def meta_wizard(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return meta_connection_wizard()


@router.post("/meta/connection-test")
async def meta_connection_test(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return await run_connection_tests()