import json
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import AdPlatform, RegionalCampaign
from app.services.marketing.capacity_engine import territory_demand_insights


@dataclass
class TerritoryCapacityInsight:
    """Legacy shape for existing routes — backed by global capacity engine."""

    territory_id: str
    territory_code: str
    territory_name: str
    appointments_next_14_days: int
    spare_capacity_score: int
    recommendation: str
    suggest_advertising: bool
    global_spare_slots: int = 0
    suggested_daily_budget_gbp: float = 0.0


async def territory_capacity_insights(db: AsyncSession) -> list[TerritoryCapacityInsight]:
    global_cap, territories = await territory_demand_insights(db)
    insights: list[TerritoryCapacityInsight] = []
    for t in territories:
        score = int((t.allocated_spare_slots / max(global_cap.spare_slots, 1)) * 100) if t.allocated_spare_slots else 0
        insights.append(
            TerritoryCapacityInsight(
                territory_id=t.territory_id,
                territory_code=t.territory_code,
                territory_name=t.territory_name,
                appointments_next_14_days=t.appointments_next_14_days,
                spare_capacity_score=score,
                recommendation=t.recommendation,
                suggest_advertising=t.recommend_advertising,
                global_spare_slots=global_cap.spare_slots,
                suggested_daily_budget_gbp=float(t.suggested_daily_budget_gbp),
            )
        )
    return insights


def propose_regional_campaigns(insights: list[TerritoryCapacityInsight]) -> list[dict]:
    proposals = []
    for i in insights:
        if not i.suggest_advertising:
            continue
        budget = i.suggested_daily_budget_gbp or (15.0 if i.spare_capacity_score >= 40 else 8.0)
        proposals.append(
            {
                "territory_code": i.territory_code,
                "territory_name": i.territory_name,
                "platform": AdPlatform.META.value,
                "suggested_daily_budget_gbp": budget,
                "headline": f"Driveway restoration in {i.territory_name}",
                "service_slug": "tarmac-restoration",
                "simulation_only": True,
                "rationale": i.recommendation,
                "spare_capacity_score": i.spare_capacity_score,
                "global_spare_slots": i.global_spare_slots,
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