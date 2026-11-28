"""Enforce owner-approved marketing spend limits."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import AdPlatform, RegionalCampaign, CampaignStatus
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
    if not daily_budget_gbp.is_finite() or daily_budget_gbp <= 0:
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
        active = (await db.execute(select(RegionalCampaign).where(RegionalCampaign.simulation_only.is_(False), RegionalCampaign.status.in_((CampaignStatus.LIVE, CampaignStatus.APPROVED, CampaignStatus.PAUSED))))).scalars().all()
        combined = daily_budget_gbp + sum((Decimal(str(c.daily_budget_gbp or 0)) for c in active), Decimal('0'))
        platform_combined = daily_budget_gbp + sum((Decimal(str(c.daily_budget_gbp or 0)) for c in active if c.platform == platform), Decimal('0'))
        platform_limit = policy.meta_daily_limit_gbp if platform == AdPlatform.META else policy.google_daily_limit_gbp
        if policy.daily_limit_gbp > 0 and combined > policy.daily_limit_gbp:
            return {"allowed": False, "reason": "Combined campaign daily budget exceeds approved limit."}
        if platform_limit > 0 and platform_combined > platform_limit:
            return {"allowed": False, "reason": "Combined platform budget exceeds approved limit."}
        if policy.monthly_limit_gbp > 0 and combined * 31 > policy.monthly_limit_gbp:
            return {"allowed": False, "reason": "Combined projected monthly budget exceeds approved limit."}
        try:
            from app.services.marketing.growth_fund import fund_summary

            fund = await fund_summary(db)
            weekly_cap = policy.weekly_limit_gbp or Decimal("150")
            if combined * 7 > weekly_cap:
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
            return {"allowed": False, "reason": "Marketing reserve verification unavailable; live spend blocked."}
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
    # These columns contain cumulative totals. Filtering by updated_at incorrectly
    # treats a recent sync of an old campaign as this week's expenditure.
    rows = (await db.scalars(select(RegionalCampaign).where(RegionalCampaign.simulation_only.is_(False)))).all()
    totals = {}
    committed = Decimal(0)
    for row in rows:
        totals[row.platform.value] = totals.get(row.platform.value, Decimal(0)) + Decimal(str(row.spent_gbp or 0))
        if row.status in (CampaignStatus.LIVE, CampaignStatus.APPROVED, CampaignStatus.PAUSED):
            committed += Decimal(str(row.daily_budget_gbp or 0))
    return {"window_days": None, "total_spent_gbp": str(sum(totals.values(), Decimal(0))), "by_platform": {k: str(v) for k, v in totals.items()}, "committed_daily_gbp": str(committed), "provisional": True, "note": "Cumulative recorded spend, conservatively counted against period limits. Dated platform billing is unavailable."}
