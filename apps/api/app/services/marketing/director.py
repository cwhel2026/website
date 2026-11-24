"""Marketing director — evidence-based weekly plan from database + capacity engine."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import AttributionEvent, RegionalCampaign
from app.models.marketing_research import MarketingResearchFinding
from app.services.marketing.capacity_engine import territory_demand_insights
from app.services.marketing.integration_registry import integration_snapshot_json


async def build_weekly_marketing_plan(db: AsyncSession) -> dict[str, Any]:
    global_cap, territories = await territory_demand_insights(db)
    since = datetime.now(UTC) - timedelta(days=7)

    spend = await db.scalar(
        select(func.coalesce(func.sum(RegionalCampaign.spent_gbp), 0))
    )
    attributions = await db.scalar(
        select(func.count()).select_from(AttributionEvent).where(AttributionEvent.landed_at >= since)
    )
    research = (
        await db.execute(
            select(MarketingResearchFinding)
            .order_by(MarketingResearchFinding.collected_at.desc())
            .limit(5)
        )
    ).scalars().all()

    proposals = []
    for t in territories:
        if not t.recommend_advertising:
            continue
        proposals.append(
            {
                "territory_code": t.territory_code,
                "territory_name": t.territory_name,
                "suggested_daily_budget_gbp": float(t.suggested_daily_budget_gbp),
                "rationale": t.recommendation,
                "demand_score": t.demand_score,
                "simulation_only": True,
            }
        )

    experiments = [
        {
            "hypothesis": "Territory headline mentioning local name improves quote starts",
            "metric": "quotations / attribution",
            "status": "proposal_only",
            "requires_approval": True,
        }
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "global_capacity": {
            k: float(v) if hasattr(v, "as_tuple") else v for k, v in global_cap.__dict__.items()
        },
        "total_ad_spend_recorded_gbp": float(spend or 0),
        "attribution_events_7d": int(attributions or 0),
        "proposed_campaign_tests": proposals,
        "experiments": experiments,
        "research_findings_on_file": [
            {
                "topic": r.topic,
                "source": r.source,
                "collected_at": r.collected_at.isoformat(),
                "confidence": float(r.confidence),
                "summary": r.summary[:240],
            }
            for r in research
        ],
        "integrations": integration_snapshot_json(),
        "disclaimer": "No external ads will launch without approval. Figures are from live database records.",
    }