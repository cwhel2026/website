"""Multi-source commercial research with dedupe, territory linkage and API budgets."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import CommercialProspect, MarketingProspectResearchRun
from app.models.territory import Territory
from app.services.marketing.budget_controls import get_or_create_budget_policy
from app.services.marketing.commercial_prospect_engine import search_companies_house
from app.services.marketing.research.google_places import search_places
from app.services.marketing.research.osm_overpass import query_commercial_features
from app.services.marketing_intelligence import commercial_lead_score
from app.services.territory_lookup import resolve_territory_for_postcode


def _dedupe_key(name: str, postcode: str | None, place_id: str | None) -> str:
    raw = f"{(name or '').lower()}|{(postcode or '').replace(' ', '')}|{place_id or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _research_spend_today(db: AsyncSession) -> Decimal:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    total = await db.scalar(
        select(func.coalesce(func.sum(MarketingProspectResearchRun.api_cost_estimate_gbp), 0)).where(
            MarketingProspectResearchRun.ran_at >= start
        )
    )
    return Decimal(str(total or 0))


async def run_territory_research(
    db: AsyncSession,
    *,
    territory_id: UUID,
    category: str,
    places_query: str,
    use_companies_house: bool = True,
    use_google_places: bool = True,
    use_osm: bool = True,
) -> dict:
    policy = await get_or_create_budget_policy(db)
    spent = await _research_spend_today(db)
    if policy.research_api_daily_limit_gbp > 0 and spent >= policy.research_api_daily_limit_gbp:
        return {"ok": False, "message": "Daily research API budget exhausted", "spent_gbp": float(spent)}

    territory = await db.get(Territory, territory_id)
    if territory is None:
        return {"ok": False, "message": "Territory not found"}

    lat = getattr(territory, "centroid_lat", None)
    lon = getattr(territory, "centroid_lon", None)
    if lat is None:
        lat, lon = 53.75, -2.7

    sources: dict = {}
    imported = 0
    cost_gbp = Decimal("0")
    ch_q = f"{category} {territory.name}"

    if use_companies_house:
        ch = await search_companies_house(db, query=ch_q, limit=15)
        sources["companies_house"] = ch
        imported += ch.get("imported", 0)

    if use_google_places:
        gp = await search_places(query=places_query or f"car park {territory.name}", latitude=lat, longitude=lon)
        sources["google_places"] = {"ok": gp.get("ok"), "count": len(gp.get("items", []))}
        cost_gbp += Decimal(str((gp.get("estimated_cost_usd") or 0) * 0.79))
        if gp.get("ok"):
            for item in gp.get("items") or []:
                name = item.get("name") or ""
                if not name:
                    continue
                place_id = item.get("place_id")
                key = _dedupe_key(name, None, place_id)
                exists = await db.execute(select(CommercialProspect).where(CommercialProspect.dedupe_key == key))
                if exists.scalar_one_or_none():
                    continue
                postcode = None
                score = commercial_lead_score(
                    has_email=False,
                    has_postcode=False,
                    category=",".join(item.get("types") or []),
                    territory_efficient=True,
                )
                prospect = CommercialProspect(
                    dedupe_key=key,
                    business_name=name[:255],
                    business_type=(item.get("types") or ["commercial"])[0][:120],
                    site_address=item.get("address"),
                    trading_premises_note="Trading premises from Google Places — registered office may differ",
                    google_place_id=place_id,
                    website=item.get("website"),
                    contact_phone=item.get("phone"),
                    territory_id=territory_id,
                    source_name=item.get("source", "Google Places"),
                    source_url=item.get("source_url"),
                    verified_on=date.today(),
                    confidence=75,
                    opportunity_category=category,
                    lead_score=score,
                    evidence_json=item,
                    lawful_basis="legitimate_interest",
                    is_corporate_subscriber=True,
                )
                db.add(prospect)
                imported += 1

    if use_osm:
        osm = await query_commercial_features(lat=lat, lon=lon)
        sources["osm"] = {"ok": osm.get("ok"), "count": len(osm.get("items", []))}
        if osm.get("ok"):
            for item in osm.get("items") or []:
                name = item.get("name") or "Commercial feature"
                pc = item.get("postcode")
                key = _dedupe_key(name, pc, item.get("osm_id"))
                exists = await db.execute(select(CommercialProspect).where(CommercialProspect.dedupe_key == key))
                if exists.scalar_one_or_none():
                    continue
                terr = await resolve_territory_for_postcode(db, pc) if pc else None
                score = commercial_lead_score(
                    has_email=False,
                    has_postcode=bool(pc),
                    category=item.get("feature_type"),
                    territory_efficient=terr is not None,
                )
                db.add(
                    CommercialProspect(
                        dedupe_key=key,
                        business_name=name[:255],
                        business_type=str(item.get("feature_type"))[:120],
                        site_address=item.get("address_hint"),
                        postcode=pc,
                        territory_id=terr.id if terr else territory_id,
                        website=item.get("website"),
                        contact_phone=item.get("phone"),
                        source_name=item.get("source", "OpenStreetMap"),
                        source_url=item.get("source_url"),
                        verified_on=date.today(),
                        confidence=55,
                        opportunity_category=category,
                        lead_score=score,
                        evidence_json={**item, "note": "Physical feature; responsible organisation not verified"},
                        lawful_basis="legitimate_interest",
                        is_corporate_subscriber=True,
                    )
                )
                imported += 1

    run = MarketingProspectResearchRun(
        territory_id=territory_id,
        category=category,
        sources_json=sources,
        imported_count=imported,
        api_cost_estimate_gbp=cost_gbp,
        status="completed",
        detail_json={"places_query": places_query},
    )
    db.add(run)
    await db.flush()
    return {
        "ok": True,
        "imported": imported,
        "api_cost_estimate_gbp": float(cost_gbp),
        "run_id": str(run.id),
        "sources": list(sources.keys()),
    }