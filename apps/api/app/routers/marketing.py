import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.approvals import ApprovalRequest, ApprovalStatus, ApprovalType
from app.models.marketing import (
    AdPlatform,
    AttributionEvent,
    CampaignStatus,
    CommercialLead,
    FlyerCampaign,
    FlyerCampaignStatus,
    MarketingIntegration,
    RegionalCampaign,
)
from app.models.user import User
from app.services.ad_adapters import integration_state_for, launch_campaign
from app.services.audit import record_audit
from app.services.marketing_intelligence import (
    check_budget_headroom,
    commercial_lead_score,
    flyer_order_pack,
    propose_regional_campaigns,
    territory_capacity_insights,
)
from app.services.territory_lookup import resolve_territory_for_postcode

router = APIRouter(prefix="/marketing", tags=["marketing"])


class CampaignIn(BaseModel):
    name: str
    platform: AdPlatform
    territory_id: UUID | None = None
    service_slug: str | None = None
    daily_budget_gbp: Decimal = Decimal("0")
    monthly_budget_gbp: Decimal = Decimal("100")
    headline: str | None = None
    body_text: str | None = None
    simulation_only: bool = True


class CampaignOut(BaseModel):
    id: UUID
    name: str
    platform: AdPlatform
    status: CampaignStatus
    simulation_only: bool
    daily_budget_gbp: Decimal
    monthly_budget_gbp: Decimal
    spent_gbp: Decimal

    class Config:
        from_attributes = True


class LeadIn(BaseModel):
    business_name: str
    address_line1: str | None = None
    town: str | None = None
    postcode: str | None = None
    website: str | None = None
    category: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    notes: str | None = None


class FlyerIn(BaseModel):
    name: str
    territory_id: UUID | None = None
    postcode_targets: str
    quantity: int = Field(gt=0)
    print_cost_gbp: Decimal = Decimal("0")
    distribution_cost_gbp: Decimal = Decimal("0")


@router.get("/integrations")
async def marketing_integrations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(select(MarketingIntegration))
    rows = list(result.scalars().all())
    if not rows:
        return [
            {"platform": p.value, "state": integration_state_for(p).value}
            for p in (AdPlatform.META, AdPlatform.GOOGLE)
        ]
    return [{"platform": r.platform.value, "state": r.state.value, "note": r.config_note} for r in rows]


@router.get("/recommendations")
async def diary_recommendations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    insights = await territory_capacity_insights(db)
    proposals = propose_regional_campaigns(insights)
    return {
        "insights": [i.__dict__ for i in insights],
        "proposed_campaigns": proposals,
    }


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[RegionalCampaign]:
    result = await db.execute(
        select(RegionalCampaign).order_by(RegionalCampaign.created_at.desc()).limit(100)
    )
    return list(result.scalars().all())


@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(
    body: CampaignIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> RegionalCampaign:
    if body.daily_budget_gbp > 0 and body.daily_budget_gbp > Decimal("50") and not body.simulation_only:
        raise HTTPException(400, "High daily budgets require simulation_only until explicitly authorised")
    campaign = RegionalCampaign(**body.model_dump(), status=CampaignStatus.DRAFT)
    db.add(campaign)
    await record_audit(
        db, actor_type="user", actor_id=str(user.id), action="marketing.create_campaign", entity_id=campaign.id
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/campaigns/{campaign_id}/request-launch")
async def request_launch(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    campaign = await db.get(RegionalCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    ok, msg = await check_budget_headroom(campaign, campaign.daily_budget_gbp or Decimal("1"))
    if not ok:
        raise HTTPException(400, msg)
    campaign.status = CampaignStatus.PENDING_APPROVAL
    db.add(
        ApprovalRequest(
            approval_type=ApprovalType.AD_SPEND,
            title=f"Launch {campaign.platform.value} campaign: {campaign.name}",
            summary=f"Daily budget £{campaign.daily_budget_gbp}; simulation={campaign.simulation_only}",
            entity_type="regional_campaign",
            entity_id=campaign.id,
            requested_by="marketing",
        )
    )
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.request_launch", entity_id=campaign.id)
    await db.commit()
    return {"message": "Approval requested", "simulation_only": campaign.simulation_only}


@router.post("/campaigns/{campaign_id}/launch-approved")
async def launch_approved(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    campaign = await db.get(RegionalCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(404)
    if campaign.status not in (CampaignStatus.APPROVED, CampaignStatus.PENDING_APPROVAL, CampaignStatus.DRAFT):
        raise HTTPException(400, "Invalid status")
    result = launch_campaign(campaign, campaign.daily_budget_gbp or Decimal("0"))
    if not result.success:
        raise HTTPException(400, result.message)
    campaign.status = CampaignStatus.LIVE_SIMULATED if result.simulation else CampaignStatus.LIVE
    campaign.external_campaign_id = result.external_id
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.launch", entity_id=campaign.id)
    await db.commit()
    return {"success": True, "simulation": result.simulation, "message": result.message}


@router.get("/commercial-leads")
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(
        select(CommercialLead).order_by(CommercialLead.score.desc()).limit(200)
    )
    return [
        {
            "id": str(l.id),
            "business_name": l.business_name,
            "postcode": l.postcode,
            "category": l.category,
            "score": l.score,
            "outreach_status": l.outreach_status.value,
            "opt_out": l.opt_out,
        }
        for l in result.scalars().all()
    ]


@router.post("/commercial-leads")
async def create_lead(
    body: LeadIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    territory = None
    if body.postcode:
        territory = await resolve_territory_for_postcode(db, body.postcode, body.town)
    score = commercial_lead_score(
        has_email=bool(body.contact_email),
        has_postcode=bool(body.postcode),
        category=body.category,
        territory_efficient=territory is not None,
    )
    lead = CommercialLead(
        **body.model_dump(),
        territory_id=territory.id if territory else None,
        score=score,
        lead_source="manual",
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return {"id": str(lead.id), "score": lead.score}


@router.get("/flyers")
async def list_flyers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(select(FlyerCampaign).order_by(FlyerCampaign.created_at.desc()).limit(50))
    return [
        {
            "id": str(f.id),
            "name": f.name,
            "qr_slug": f.qr_slug,
            "status": f.status.value,
            "quantity": f.quantity,
        }
        for f in result.scalars().all()
    ]


@router.post("/flyers")
async def create_flyer(
    body: FlyerIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    slug = secrets.token_hex(4)
    flyer = FlyerCampaign(
        name=body.name,
        territory_id=body.territory_id,
        postcode_targets=body.postcode_targets,
        quantity=body.quantity,
        print_cost_gbp=body.print_cost_gbp,
        distribution_cost_gbp=body.distribution_cost_gbp,
        qr_slug=slug,
        landing_path=f"/c/{slug}",
        status=FlyerCampaignStatus.DRAFT,
    )
    db.add(flyer)
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.create_flyer", entity_id=flyer.id)
    await db.commit()
    return {"id": str(flyer.id), "qr_slug": slug, "landing_path": flyer.landing_path}


@router.post("/flyers/{flyer_id}/order-pack")
async def flyer_pack(
    flyer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    flyer = await db.get(FlyerCampaign, flyer_id)
    if flyer is None:
        raise HTTPException(404)
    flyer.status = FlyerCampaignStatus.ORDER_PACK_READY
    pack = flyer_order_pack(flyer)
    await db.commit()
    return {"order_pack_json": pack}


class AttributionIn(BaseModel):
    source: str
    medium: str = "unknown"
    content: str | None = None
    campaign_id: UUID | None = None
    flyer_campaign_id: UUID | None = None


@router.post("/attribution/track")
async def track_attribution(
    body: AttributionIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    db.add(
        AttributionEvent(
            source=body.source,
            medium=body.medium,
            content=body.content,
            campaign_id=body.campaign_id,
            flyer_campaign_id=body.flyer_campaign_id,
        )
    )
    await db.commit()
    return {"status": "recorded"}