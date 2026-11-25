"""Territory opportunity scores from operational + CRM signals."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import AttributionEvent
from app.models.quotation import Quotation
from app.models.marketing_ops import TerritoryIntelligenceScore
from app.models.territory import Territory
from app.services.marketing.capacity_engine import territory_demand_insights


async def recompute_territory_intelligence(db: AsyncSession) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=90)
    global_cap, capacity_rows = await territory_demand_insights(db)
    territories = (await db.execute(select(Territory).where(Territory.is_active.is_(True)))).scalars().all()
    capacity_by_id = {str(r.territory_id): r for r in capacity_rows}
    out: list[dict] = []

    for territory in territories:
        cap = capacity_by_id.get(str(territory.id))
        enquiry_count = await db.scalar(
            select(func.count())
            .select_from(Quotation)
            .where(Quotation.territory_id == territory.id, Quotation.created_at >= since)
        )
        attributions = await db.scalar(
            select(func.count())
            .select_from(AttributionEvent)
            .where(AttributionEvent.landed_at >= since)
        )
        demand = min(100, int(enquiry_count or 0) * 8)
        opportunity = demand
        if cap and cap.recommend_advertising:
            opportunity += 25
        if cap and not cap.recommend_advertising:
            opportunity -= 20
        competition = 40
        opportunity = max(0, min(100, opportunity))
        action = (
            cap.recommendation
            if cap
            else "Insufficient capacity data — run capacity snapshot task."
        )
        evidence = {
            "enquiries_90d": int(enquiry_count or 0),
            "attributions_90d_total_network": int(attributions or 0),
            "global_spare_slots": global_cap.spare_slots,
            "verified": ["quotation counts by territory", "capacity engine"],
            "estimate": ["competition_indicator baseline"],
        }
        existing = await db.execute(
            select(TerritoryIntelligenceScore).where(
                TerritoryIntelligenceScore.territory_id == territory.id
            )
        )
        row = existing.scalar_one_or_none()
        if row is None:
            row = TerritoryIntelligenceScore(territory_id=territory.id)
            db.add(row)
        row.opportunity_score = opportunity
        row.demand_indicator = demand
        row.competition_indicator = competition
        row.recommended_action = action
        row.evidence_json = evidence
        row.computed_at = datetime.now(UTC)
        out.append(
            {
                "territory_code": territory.code,
                "territory_name": territory.name,
                "opportunity_score": opportunity,
                "demand_indicator": demand,
                "competition_indicator": competition,
                "recommended_action": action,
                "confidence": "mixed",
                "computed_at": row.computed_at.isoformat(),
            }
        )
    await db.flush()
    return out


async def list_territory_intelligence(db: AsyncSession) -> list[dict]:
    rows = (
        await db.execute(
            select(TerritoryIntelligenceScore, Territory)
            .join(Territory, Territory.id == TerritoryIntelligenceScore.territory_id)
            .order_by(TerritoryIntelligenceScore.opportunity_score.desc())
        )
    ).all()
    if not rows:
        return await recompute_territory_intelligence(db)
    return [
        {
            "territory_code": t.code,
            "territory_name": t.name,
            "opportunity_score": s.opportunity_score,
            "demand_indicator": s.demand_indicator,
            "competition_indicator": s.competition_indicator,
            "recommended_action": s.recommended_action,
            "evidence": s.evidence_json,
            "computed_at": s.computed_at.isoformat(),
        }
        for s, t in rows
    ]