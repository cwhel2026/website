import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Appointment
from app.models.marketing import AdPlatform, RegionalCampaign
from app.models.territory import Territory


@dataclass
class TerritoryCapacityInsight:
    territory_id: str
    territory_code: str
    territory_name: str
    appointments_next_14_days: int
    spare_capacity_score: int
    recommendation: str
    suggest_advertising: bool


async def territory_capacity_insights(db: AsyncSession) -> list[TerritoryCapacityInsight]:
    now = datetime.now(UTC)
    window_end = now + timedelta(days=14)
    territories = (await db.execute(select(Territory).where(Territory.is_active.is_(True)))).scalars().all()
    insights: list[TerritoryCapacityInsight] = []

    from app.models.jobs import Job

    for t in territories:
        count_result = await db.execute(
            select(func.count())
            .select_from(Appointment)
            .join(Job)
            .where(
                Job.territory_id == t.id,
                Appointment.scheduled_start >= now,
                Appointment.scheduled_start < window_end,
            )
        )
        appt_count = count_result.scalar() or 0
        # Heuristic: owner solo ~10 slots per 14 days practical
        max_slots = 12
        spare = max(0, max_slots - appt_count)
        score = int((spare / max_slots) * 100)
        suggest = spare >= 4
        if appt_count >= max_slots:
            rec = "Pause or reduce campaigns — diary near capacity."
            suggest = False
        elif spare >= 6:
            rec = "Good window for targeted regional advertising."
        elif spare >= 2:
            rec = "Limited capacity — small test budget only."
        else:
            rec = "Low spare capacity — avoid increasing demand."

        insights.append(
            TerritoryCapacityInsight(
                territory_id=str(t.id),
                territory_code=t.code,
                territory_name=t.name,
                appointments_next_14_days=appt_count,
                spare_capacity_score=score,
                recommendation=rec,
                suggest_advertising=suggest,
            )
        )
    return insights


def propose_regional_campaigns(insights: list[TerritoryCapacityInsight]) -> list[dict]:
    proposals = []
    for i in insights:
        if not i.suggest_advertising:
            continue
        proposals.append(
            {
                "territory_code": i.territory_code,
                "territory_name": i.territory_name,
                "platform": AdPlatform.META.value,
                "suggested_daily_budget_gbp": 15.0 if i.spare_capacity_score >= 50 else 8.0,
                "headline": f"Driveway restoration in {i.territory_name}",
                "service_slug": "tarmac-driveway-restoration",
                "simulation_only": True,
                "rationale": i.recommendation,
                "spare_capacity_score": i.spare_capacity_score,
            }
        )
    return proposals


async def check_budget_headroom(campaign: RegionalCampaign, amount: Decimal) -> tuple[bool, str]:
    if amount <= 0:
        return False, "Amount must be positive"
    if campaign.daily_budget_gbp > 0 and amount > campaign.daily_budget_gbp:
        return False, "Exceeds daily budget"
    if campaign.monthly_budget_gbp > 0 and campaign.spent_gbp + amount > campaign.monthly_budget_gbp:
        return False, "Exceeds monthly budget"
    return True, "OK"


def commercial_lead_score(
    *,
    has_email: bool,
    has_postcode: bool,
    category: str | None,
    territory_efficient: bool,
) -> int:
    score = 0
    if has_email:
        score += 20
    if has_postcode:
        score += 15
    if category and any(
        k in category.lower()
        for k in ("car park", "hotel", "retail", "industrial", "property management")
    ):
        score += 35
    if territory_efficient:
        score += 20
    return min(100, score)


def flyer_order_pack(flyer) -> str:
    return json.dumps(
        {
            "campaign": flyer.name,
            "qty": flyer.quantity,
            "postcodes": flyer.postcode_targets,
            "qr_url_path": f"/c/{flyer.qr_slug}",
            "print_cost_gbp": float(flyer.print_cost_gbp),
            "distribution_cost_gbp": float(flyer.distribution_cost_gbp),
            "note": "Manual submission pack — no print API connected",
        },
        indent=2,
    )