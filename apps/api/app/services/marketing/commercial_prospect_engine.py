"""Commercial prospect discovery — Companies House API (legitimate UK source)."""

from __future__ import annotations

import hashlib
from datetime import date
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.marketing_ops import CommercialProspect
from app.services.marketing_intelligence import commercial_lead_score
from app.services.territory_lookup import resolve_territory_for_postcode


def _dedupe_key(name: str, postcode: str | None) -> str:
    raw = f"{name.lower().strip()}|{(postcode or '').lower().replace(' ', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def search_companies_house(db: AsyncSession, *, query: str, limit: int = 20) -> dict:
    settings = get_settings()
    api_key = getattr(settings, "companies_house_api_key", None)
    if not api_key:
        return {
            "ok": False,
            "message": "COMPANIES_HOUSE_API_KEY not set — add to Railway for UK company search.",
            "source": "https://developer.company-information.service.gov.uk/",
        }
    url = f"https://api.company-information.service.gov.uk/search/companies?q={quote(query)}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, auth=(api_key, ""))
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        return {"ok": False, "message": str(exc)[:300]}

    imported = 0
    skipped = 0
    for item in (payload.get("items") or [])[:limit]:
        name = item.get("title") or ""
        if not name:
            continue
        addr = item.get("address") or {}
        postcode = addr.get("postal_code")
        key = _dedupe_key(name, postcode)
        existing = await db.execute(select(CommercialProspect).where(CommercialProspect.dedupe_key == key))
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        territory = await resolve_territory_for_postcode(db, postcode) if postcode else None
        score = commercial_lead_score(
            has_email=False,
            has_postcode=bool(postcode),
            category=item.get("description"),
            territory_efficient=territory is not None,
        )
        prospect = CommercialProspect(
            dedupe_key=key,
            business_name=name[:255],
            business_type=(item.get("description") or "")[:120] or None,
            site_address=", ".join(
                x for x in (addr.get("address_line_1"), addr.get("locality")) if x
            )[:500]
            or None,
            postcode=postcode,
            territory_id=territory.id if territory else None,
            source_name="Companies House API",
            source_url=f"https://find-and-update.company-information.service.gov.uk/company/{item.get('company_number')}",
            verified_on=date.today(),
            confidence=70,
            opportunity_category="commercial_surface",
            lead_score=score,
            evidence_json={"company_number": item.get("company_number"), "raw_status": item.get("company_status")},
            lawful_basis="legitimate_interest",
            is_corporate_subscriber=True,
        )
        db.add(prospect)
        imported += 1
    await db.flush()
    return {
        "ok": True,
        "imported": imported,
        "skipped_duplicates": skipped,
        "query": query,
        "source": "Companies House Search API",
        "verified_on": date.today().isoformat(),
    }