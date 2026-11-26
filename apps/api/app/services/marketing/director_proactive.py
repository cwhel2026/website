"""Proactive marketing director — persistent runs with evidence labels."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import CommercialProspect, MarketingDirectorRun
from app.models.territory import Territory
from app.services.marketing.capacity_engine import territory_demand_insights
from app.services.marketing.director import build_weekly_marketing_plan
from app.services.marketing.integration_setup import build_integration_centre
from app.services.marketing.competitor_research import list_competitor_findings
from app.services.marketing.profitability_full import marketing_profitability_full
from app.services.marketing.prospect_categories import TERRITORY_AREAS, vertical_places_queries
from app.services.marketing.research.prospect_orchestrator import run_territory_research


async def record_director_run(
    db: AsyncSession,
    *,
    run_type: str,
    summary: str,
    recommendations: list[dict],
    evidence: dict,
    pre_launch: bool = True,
) -> MarketingDirectorRun:
    row = MarketingDirectorRun(
        run_type=run_type,
        summary=summary,
        recommendations_json=recommendations,
        evidence_json=evidence,
        pre_launch_mode=pre_launch,
    )
    db.add(row)
    await db.flush()
    return row


async def run_daily_director_cycle(db: AsyncSession, *, execute_research: bool = False) -> dict[str, Any]:
    integrations = build_integration_centre()
    pre_launch = not any(
        i.get("live_write_verified") for i in integrations["integrations"] if isinstance(i, dict)
    )
    weekly = await build_weekly_marketing_plan(db)
    profit = await marketing_profitability_full(db, days=30)
    competitor_rows = await list_competitor_findings(db, limit=8)
    global_cap, territories = await territory_demand_insights(db)

    cluster_opportunities: list[dict] = []
    for t in territories:
        if t.appointments_next_14_days >= 2 and t.recommend_advertising:
            cluster_opportunities.append(
                {
                    "territory": t.territory_name,
                    "appointments_14d": t.appointments_next_14_days,
                    "action": f"Add nearby domestic/commercial campaigns around {t.territory_name}",
                    "certainty": "verified",
                    "rationale": t.recommendation,
                }
            )

    underserved = [
        {
            "territory": t.territory_name,
            "demand_score": t.demand_score,
            "spare_allocation": t.allocated_spare_slots,
            "certainty": "estimate",
        }
        for t in territories
        if t.recommend_advertising and t.demand_score >= 40
    ][:5]

    research_evidence: dict[str, Any] = {"scheduled_queries": []}
    if execute_research:
        terr = (
            await db.execute(select(Territory).where(Territory.is_active.is_(True)).order_by(Territory.code).limit(1))
        ).scalar_one_or_none()
        if terr:
            area = next((a for a in TERRITORY_AREAS if a.lower() in terr.name.lower()), terr.name)
            q = vertical_places_queries("retail_park", area)[0]
            research_evidence["scheduled_queries"].append(q)
            if not pre_launch or integrations:
                res = await run_territory_research(
                    db,
                    territory_id=terr.id,
                    category="retail_park",
                    places_query=q,
                    use_google_places=bool(__import__("app.config", fromlist=["get_settings"]).get_settings().google_places_api_key),
                )
                research_evidence["last_research"] = res

    prospect_backlog = await db.scalar(select(func.count()).select_from(CommercialProspect))
    competitor_note = {
        "method": "Google Places listings when API key configured — no invented pricing",
        "certainty": "verified" if competitor_rows else "estimate",
        "prospect_records": int(prospect_backlog or 0),
        "recent_findings": competitor_rows[:5],
    }

    seasonal = {
        "window": "Late autumn — coating weather sensitivity",
        "recommendation": "Prioritise pressure washing slots; coat within 7 days when forecast allows",
        "certainty": "verified",
    }

    recommendations: list[dict] = []
    if pre_launch:
        recommendations.append(
            {
                "action": "Complete pre-launch checklist — connect Meta/Google when business accounts exist",
                "certainty": "verified",
            }
        )
    recommendations.extend(cluster_opportunities[:3])
    for u in underserved[:2]:
        recommendations.append(
            {
                "action": f"Prospect commercial sites in {u['territory']}",
                "reason": f"Demand score {u['demand_score']}",
                "certainty": "estimate",
            }
        )
    if competitor_rows and not pre_launch:
        recommendations.append(
            {
                "action": f"Review {len(competitor_rows)} competitor intelligence rows before local campaigns",
                "certainty": "verified",
            }
        )
    if profit.get("marketing_roi") is not None and profit.get("marketing_roi", 0) < 1:
        recommendations.append(
            {
                "action": "Pause low-ROI campaigns — optimise for completed profitable jobs",
                "reason": f"Marketing ROI {profit.get('marketing_roi')}",
                "certainty": "estimate",
            }
        )

    summary = (
        f"Pre-launch={pre_launch}. Spare capacity {global_cap.spare_slots}. "
        f"Prospects on file: {prospect_backlog}. Attribution-linked profit provisional."
    )
    evidence = {
        "integrations_checked": integrations["checked_at"],
        "competitor_intel": competitor_note,
        "seasonal": seasonal,
        "profitability_30d": profit,
        "research": research_evidence,
        "weekly_plan_excerpt": {
            "proposals": len(weekly.get("proposed_campaign_tests", [])),
            "attribution_7d": weekly.get("attribution_events_7d"),
        },
    }
    row = await record_director_run(
        db, run_type="daily", summary=summary, recommendations=recommendations, evidence=evidence, pre_launch=pre_launch
    )
    return {
        "run_id": str(row.id),
        "pre_launch_mode": pre_launch,
        "summary": summary,
        "recommendations": recommendations,
        "evidence": evidence,
        "disclaimer": "Estimates labelled; no external ads without approval.",
    }


async def list_director_history(db: AsyncSession, limit: int = 30) -> list[dict]:
    rows = (
        await db.execute(
            select(MarketingDirectorRun).order_by(MarketingDirectorRun.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "run_type": r.run_type,
            "summary": r.summary,
            "created_at": r.created_at.isoformat(),
            "pre_launch_mode": r.pre_launch_mode,
            "recommendations": r.recommendations_json,
        }
        for r in rows
    ]