"""Enforce owner-approved marketing spend limits."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import AdPlatform, RegionalCampaign
from app.models.marketing_ops import MarketingBudgetPolicy


async def emergency_pause_connected_platforms() -> dict:
    from app.services.marketing.google_ads.google_ads_service import GoogleAdsClient
    from app.services.marketing.meta.meta_campaign_service import pause_all_campaigns

    meta = await pause_all_campaigns()
    google = await (GoogleAdsClient().pause_all_active())
    return {"meta": meta, "google_ads": {"ok": google.ok, "message": google.message, "payload": google.payload}}


async def get_or_create_budget_policy(db: AsyncSession) -> MarketingBudgetPolicy:
    row = await db.execute(select(MarketingBudgetPolicy).limit(1))
    policy = row.scalar_one_or_none()
    if policy is None:
        policy = MarketingBudgetPolicy()
        policy.geo_target_json = {
            "centre": "Preston, Lancashire",
            "radius_miles": 20,
        }
        db.add(policy)
        await db.flush()
    return policy


async def committed_spend_today(db: AsyncSession) -> Decimal:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.scalar(
        select(func.coalesce(func.sum(RegionalCampaign.spent_gbp), 0)).where(
            RegionalCampaign.updated_at >= start
        )
    )
    return Decimal(str(result or 0))


async def validate_campaign_spend(
    db: AsyncSession,
    *,
    platform: AdPlatform,
    daily_budget_gbp: Decimal,
    simulation_only: bool,
) -> dict:
    policy = await get_or_create_budget_policy(db)
    if policy.emergency_pause_all:
        return {"allowed": False, "reason": "Emergency pause is active for all paid marketing."}
    if not simulation_only and not policy.live_paid_spend_approved:
        return {
            "allowed": False,
            "reason": "Live paid spend is not approved — enable in Marketing → Budget controls.",
        }
    if daily_budget_gbp <= 0:
        return {"allowed": False, "reason": "Budget must be greater than zero."}
    if policy.daily_limit_gbp > 0 and daily_budget_gbp > policy.daily_limit_gbp:
        return {"allowed": False, "reason": "Exceeds overall daily limit."}
    if platform == AdPlatform.META and policy.meta_daily_limit_gbp > 0:
        if daily_budget_gbp > policy.meta_daily_limit_gbp:
            return {"allowed": False, "reason": "Exceeds Meta daily limit."}
    if platform == AdPlatform.GOOGLE and policy.google_daily_limit_gbp > 0:
        if daily_budget_gbp > policy.google_daily_limit_gbp:
            return {"allowed": False, "reason": "Exceeds Google daily limit."}
    today = await committed_spend_today(db)
    if policy.daily_limit_gbp > 0 and today + daily_budget_gbp > policy.daily_limit_gbp:
        return {"allowed": False, "reason": f"Would exceed today's committed spend (£{today})."}
    if not simulation_only:
        try:
            from app.services.marketing.growth_fund import fund_summary

            fund = await fund_summary(db)
            weekly_cap = policy.weekly_limit_gbp or Decimal("150")
            if daily_budget_gbp * 7 > weekly_cap:
                return {
                    "allowed": False,
                    "reason": f"Exceeds approved weekly advertising limit (£{weekly_cap}). "
                    "Increase only with explicit owner approval.",
                }
            if fund["available_uncommitted_gbp"] < float(daily_budget_gbp * 7):
                return {
                    "allowed": False,
                    "reason": "Insufficient virtual marketing fund for this commitment "
                    f"(available £{fund['available_uncommitted_gbp']:.2f}).",
                }
        except Exception:
            pass
    return {"allowed": True, "policy": _policy_dict(policy)}


def _policy_dict(policy: MarketingBudgetPolicy) -> dict:
    return {
        "live_paid_spend_approved": policy.live_paid_spend_approved,
        "emergency_pause_all": policy.emergency_pause_all,
        "daily_limit_gbp": float(policy.daily_limit_gbp),
        "weekly_limit_gbp": float(policy.weekly_limit_gbp),
        "monthly_limit_gbp": float(policy.monthly_limit_gbp),
        "meta_daily_limit_gbp": float(policy.meta_daily_limit_gbp),
        "meta_weekly_budget_gbp": float(getattr(policy, "meta_weekly_budget_gbp", 150)),
        "meta_safety_buffer_pct": float(getattr(policy, "meta_safety_buffer_pct", 5)),
        "director_operating_mode": getattr(getattr(policy, "director_operating_mode", None), "value", "recommend"),
        "google_daily_limit_gbp": float(policy.google_daily_limit_gbp),
        "research_api_daily_limit_gbp": float(policy.research_api_daily_limit_gbp),
        "outreach_email_enabled": policy.outreach_email_enabled,
        "outreach_daily_cap": policy.outreach_daily_cap,
        "geo_target": getattr(policy, "geo_target_json", None),
    }


async def weekly_spend_summary(db: AsyncSession) -> dict:
    since = datetime.now(UTC) - timedelta(days=7)
    total = await db.scalar(
        select(func.coalesce(func.sum(RegionalCampaign.spent_gbp), 0)).where(
            RegionalCampaign.updated_at >= since
        )
    )
    by_platform = await db.execute(
        select(RegionalCampaign.platform, func.coalesce(func.sum(RegionalCampaign.spent_gbp), 0))
        .where(RegionalCampaign.updated_at >= since)
        .group_by(RegionalCampaign.platform)
    )
    return {
        "window_days": 7,
        "total_spent_gbp": float(total or 0),
        "by_platform": {row[0].value: float(row[1]) for row in by_platform.all()},
        "provisional": True,
        "note": "Relies on campaign spent_gbp sync — verify against ad platform billing.",
    }