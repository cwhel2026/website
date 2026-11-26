"""Central brand intelligence — used by all marketing AI."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import MarketingBrandProfile

DEFAULT_AREAS = [
    "Lancashire",
    "Blackpool",
    "Preston",
    "Southport",
    "Liverpool",
    "Manchester",
    "Blackburn",
    "Wigan",
    "Bolton",
    "Warrington",
]

DEFAULT_CLAIMS = [
    "Professional driveway and commercial surface restoration",
    "Pressure washing and protective coatings where suitable",
    "North West England service coverage",
]

DEFAULT_CTAS = ["Request a free quotation at revivemydrive.co.uk", "Call for a site assessment"]


async def get_or_create_brand(db: AsyncSession) -> MarketingBrandProfile:
    row = (await db.execute(select(MarketingBrandProfile).limit(1))).scalar_one_or_none()
    if row is None:
        row = MarketingBrandProfile(
            business_name="SurfaceCoat Ltd",
            primary_colour="#1a1a1a",
            secondary_colour="#eab308",
            tagline="Driveway & commercial surface restoration — Preston, Lancashire",
            service_areas_json=DEFAULT_AREAS,
            approved_claims_json=DEFAULT_CLAIMS,
            approved_ctas_json=DEFAULT_CTAS,
            tone_of_voice="Professional, plain English, never guarantee savings or fabricate results.",
            differentiators_json=["Restoration before resurfacing where appropriate", "Owner-operated quality control"],
            objectives_json={"domestic": "Fill diary with profitable restoration jobs", "commercial": "B2B car park and forecourt contracts"},
            demographics_json={"domestic": "Homeowners with tarmac/block paving", "commercial": "Retail, hospitality, FM"},
            photo_permission_policy="Only publish customer photos with explicit permission recorded on the job.",
            services_summary="Tarmac restoration, block paving restoration, pressure washing, commercial car parks.",
        )
        db.add(row)
        await db.flush()
    return row


def brand_system_prompt(brand: MarketingBrandProfile) -> str:
    return (
        f"You write for {brand.business_name}. "
        f"Tone: {brand.tone_of_voice or 'professional'}. "
        f"Approved claims only: {brand.approved_claims_json or DEFAULT_CLAIMS}. "
        f"CTAs: {brand.approved_ctas_json or DEFAULT_CTAS}. "
        f"Areas: {', '.join(brand.service_areas_json or DEFAULT_AREAS)}. "
        "Never invent testimonials or before/after results."
    )


async def brand_json(db: AsyncSession) -> dict:
    b = await get_or_create_brand(db)
    return {
        "business_name": b.business_name,
        "phone": b.phone,
        "website": b.website,
        "tagline": b.tagline,
        "colours": {"primary": b.primary_colour, "secondary": b.secondary_colour},
        "service_areas": b.service_areas_json,
        "tone_of_voice": b.tone_of_voice,
        "approved_claims": b.approved_claims_json,
        "approved_ctas": b.approved_ctas_json,
        "objectives": b.objectives_json,
        "differentiators": b.differentiators_json,
        "photo_permission_policy": b.photo_permission_policy,
    }