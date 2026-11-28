"""30-day launch campaign planner — drafts only until approval."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import MarketingLaunchPlan
from app.services.marketing.budget_controls import get_or_create_budget_policy


async def generate_launch_plan(db: AsyncSession, *, launch_date: date | None = None) -> dict:
    policy = await get_or_create_budget_policy(db)
    launch = launch_date or policy.official_launch_date
    if launch is None:
        launch = datetime.now(ZoneInfo("Europe/London")).date()
    policy.official_launch_date = launch
    weeks = []
    for w in range(4):
        start = launch + timedelta(days=w * 7)
        weeks.append(
            {
                "week": w + 1,
                "start": start.isoformat(),
                "tasks": [
                    {"type": "content", "action": "3× Facebook drafts (approval)", "simulation_only": True},
                    {"type": "commercial", "action": "Territory prospect research batch", "simulation_only": True},
                    {"type": "seo", "action": "Local service page review — no doorway pages", "simulation_only": True},
                    {"type": "gpb", "action": "GBP setup when account exists", "blocked_until": "gbp_account"},
                ],
                "budget_scenarios": [
                    {"label": "Conservative", "daily_gbp": 5, "simulation_only": True},
                    {"label": "Growth", "daily_gbp": 15, "requires_approval": True},
                ],
                "experiments": [{"hypothesis": "Local headline in Preston", "metric": "qualified enquiries"}],
            }
        )
    plan = {
        "launch_date": launch.isoformat(),
        "pre_launch": launch > datetime.now(ZoneInfo("Europe/London")).date(),
        "weeks": weeks,
        "disclaimer": "No publish or live spend until owner approval",
    }
    row = MarketingLaunchPlan(launch_date=launch, plan_json=plan)
    db.add(row)
    await db.flush()
    return {"plan_id": str(row.id), **plan}


async def latest_launch_plan(db: AsyncSession) -> dict | None:
    row = (await db.execute(select(MarketingLaunchPlan).order_by(MarketingLaunchPlan.generated_at.desc()).limit(1))).scalar_one_or_none()
    if not row:
        return None
    return {"plan_id": str(row.id), "launch_date": row.launch_date.isoformat() if row.launch_date else None, **(row.plan_json or {})}