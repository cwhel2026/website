import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.rate_limit import limiter
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
from app.models.marketing_experiment import MarketingExperiment
from app.models.marketing_research import MarketingResearchFinding
from app.services.marketing.capacity_engine import territory_demand_insights
from app.models.marketing_ops import CommercialProspect, MarketingBudgetPolicy, OutreachMessage, OutreachMessageStatus
from app.services.marketing.budget_controls import (
    emergency_pause_connected_platforms,
    get_or_create_budget_policy,
    validate_campaign_spend,
    weekly_spend_summary,
)
from app.services.marketing.email.outreach_mailer import approve_and_send
from app.services.marketing.research.prospect_orchestrator import run_territory_research
from app.services.marketing.commercial_prospect_engine import search_companies_house
from app.services.marketing.director import build_daily_marketing_plan, build_weekly_marketing_plan
from app.services.marketing.marketing_profitability import marketing_profitability_snapshot
from app.services.marketing.meta_ads_client import fetch_account_insights
from app.services.marketing.outreach_compliance import create_outreach_draft
from app.services.marketing.territory_intelligence import list_territory_intelligence, recompute_territory_intelligence
from app.services.marketing.integration_registry import integration_snapshot_json
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
    name: str = Field(min_length=1, max_length=200)
    platform: AdPlatform
    territory_id: UUID | None = None
    service_slug: str | None = None
    daily_budget_gbp: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    monthly_budget_gbp: Decimal = Field(default=Decimal("100"), ge=0, max_digits=12, decimal_places=2)
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


@router.get("/capacity")
async def marketing_global_capacity(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    global_cap, territories = await territory_demand_insights(db)
    return {
        "global": {
            k: float(v) if hasattr(v, "as_tuple") else v for k, v in global_cap.__dict__.items()
        },
        "territories": [
            {
                **{k: float(v) if hasattr(v, "as_tuple") else v for k, v in t.__dict__.items()},
            }
            for t in territories
        ],
    }


@router.get("/platform-status")
async def marketing_platform_status(
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return integration_snapshot_json()


@router.get("/director/weekly-plan")
async def marketing_director_weekly_plan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await build_weekly_marketing_plan(db)


@router.get("/director/daily-plan")
async def marketing_director_daily_plan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await build_daily_marketing_plan(db)


class BudgetPolicyUpdate(BaseModel):
    live_paid_spend_approved: bool | None = None
    emergency_pause_all: bool | None = None
    daily_limit_gbp: Decimal | None = None
    weekly_limit_gbp: Decimal | None = None
    monthly_limit_gbp: Decimal | None = None
    meta_daily_limit_gbp: Decimal | None = None
    google_daily_limit_gbp: Decimal | None = None
    research_api_daily_limit_gbp: Decimal | None = None
    outreach_email_enabled: bool | None = None
    outreach_daily_cap: int | None = None


@router.get("/budget")
async def get_marketing_budget(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    spend = await weekly_spend_summary(db)
    return {
        "policy": _policy_dict(policy),
        "weekly_spend": spend,
    }


def _policy_dict(policy: MarketingBudgetPolicy) -> dict:
    return {
        "live_paid_spend_approved": policy.live_paid_spend_approved,
        "emergency_pause_all": policy.emergency_pause_all,
        "daily_limit_gbp": float(policy.daily_limit_gbp),
        "weekly_limit_gbp": float(policy.weekly_limit_gbp),
        "monthly_limit_gbp": float(policy.monthly_limit_gbp),
        "meta_daily_limit_gbp": float(policy.meta_daily_limit_gbp),
        "google_daily_limit_gbp": float(policy.google_daily_limit_gbp),
        "research_api_daily_limit_gbp": float(policy.research_api_daily_limit_gbp),
        "outreach_email_enabled": policy.outreach_email_enabled,
        "outreach_daily_cap": policy.outreach_daily_cap,
    }


@router.patch("/budget")
async def patch_marketing_budget(
    body: BudgetPolicyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    await db.refresh(policy, with_for_update=True)
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None or (isinstance(value, Decimal) and (not value.is_finite() or value < 0)) or (field == "outreach_daily_cap" and value < 0):
            raise HTTPException(422, "Invalid budget policy value")
        setattr(policy, field, value)
    await record_audit(
        db, actor_type="user", actor_id=str(user.id), action="marketing.budget_update", entity_id=policy.id
    )
    await db.commit()
    return {"policy": _policy_dict(policy)}


@router.get("/profitability")
async def marketing_profitability(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 30,
) -> dict:
    return await marketing_profitability_snapshot(db, days=days)


@router.get("/territory-intelligence")
async def territory_intelligence(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    refresh: bool = False,
) -> dict:
    rows = await recompute_territory_intelligence(db) if refresh else await list_territory_intelligence(db)
    await db.commit()
    return {"territories": rows}


@router.get("/meta/insights")
async def meta_insights(
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await fetch_account_insights()


class ProspectSearchIn(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=20, le=50)


@router.post("/commercial-prospects/search")
async def commercial_prospect_search(
    body: ProspectSearchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    result = await search_companies_house(db, query=body.query, limit=body.limit)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="marketing.ch_search",
        entity_id=None,
    )
    await db.commit()
    return result


@router.get("/commercial-prospects")
async def list_commercial_prospects(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = (
        await db.execute(
            select(CommercialProspect).order_by(CommercialProspect.lead_score.desc()).limit(200)
        )
    ).scalars().all()
    return [
        {
            "id": str(p.id),
            "business_name": p.business_name,
            "postcode": p.postcode,
            "lead_score": p.lead_score,
            "source_name": p.source_name,
            "verified_on": p.verified_on.isoformat() if p.verified_on else None,
            "confidence": p.confidence,
            "outreach_status": p.outreach_status.value,
            "pipeline_stage": p.pipeline_stage.value,
            "priority_score": p.priority_score,
            "opt_out": p.opt_out,
        }
        for p in rows
    ]


@router.post("/commercial-prospects/{prospect_id}/outreach-draft")
async def outreach_draft(
    prospect_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    prospect = await db.get(CommercialProspect, prospect_id)
    if prospect is None:
        raise HTTPException(404, "Prospect not found")
    msg, detail = await create_outreach_draft(db, prospect)
    if msg is None:
        raise HTTPException(400, detail)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="marketing.outreach_draft",
        entity_id=msg.id,
    )
    await db.commit()
    return {"message_id": str(msg.id), "status": msg.status.value, "detail": detail}


class ResearchFindingIn(BaseModel):
    topic: str
    category: str = "general"
    source: str
    source_url: str | None = None
    confidence: float = Field(ge=0, le=1, default=0.5)
    summary: str
    payload_json: str = "{}"


@router.get("/research")
async def list_research_findings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = (
        await db.execute(
            select(MarketingResearchFinding).order_by(MarketingResearchFinding.collected_at.desc()).limit(100)
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "topic": r.topic,
            "source": r.source,
            "collected_at": r.collected_at.isoformat(),
            "confidence": float(r.confidence),
            "summary": r.summary,
        }
        for r in rows
    ]


@router.post("/research")
async def create_research_finding(
    body: ResearchFindingIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    row = MarketingResearchFinding(
        topic=body.topic,
        category=body.category,
        source=body.source,
        source_url=body.source_url,
        collected_at=datetime.now(UTC),
        confidence=body.confidence,
        summary=body.summary,
        payload_json=body.payload_json,
    )
    db.add(row)
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.research_record", entity_id=row.id)
    await db.commit()
    return {"id": str(row.id), "message": "Research finding recorded with source metadata."}


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
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> RegionalCampaign:
    gate = await validate_campaign_spend(
        db,
        platform=body.platform,
        daily_budget_gbp=body.daily_budget_gbp or Decimal("0"),
        simulation_only=body.simulation_only,
    )
    if not gate.get("allowed") and (body.daily_budget_gbp or 0) > 0:
        raise HTTPException(400, gate.get("reason", "Budget blocked"))
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
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    campaign = await db.get(RegionalCampaign, campaign_id, with_for_update=True)
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.PROPOSED):
        raise HTTPException(409, "Only draft or proposed campaigns can request launch")
    ok, msg = await check_budget_headroom(db, campaign, campaign.daily_budget_gbp or Decimal("1"))
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
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    campaign = await db.get(RegionalCampaign, campaign_id, with_for_update=True)
    if campaign is None:
        raise HTTPException(404)
    if campaign.status != CampaignStatus.APPROVED:
        raise HTTPException(
            409, "Campaign must be approved in Approvals before launch (current status: %s)" % campaign.status.value
        )
    if not campaign.simulation_only:
        raise HTTPException(409, "Live launch requires verified provider execution and spend controls")
    result = launch_campaign(campaign, campaign.daily_budget_gbp or Decimal("0"))
    if not result.success:
        raise HTTPException(400, result.message)
    campaign.status = CampaignStatus.LIVE_SIMULATED if result.simulation else CampaignStatus.LIVE
    campaign.external_campaign_id = result.external_id
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.launch", entity_id=campaign.id)
    await db.commit()
    if result.simulation:
        return {
            "success": True,
            "live": False,
            "simulation": True,
            "message": "SIMULATED ONLY — nothing was sent to the ad platform and no money was spent. " + result.message,
        }
    return {"success": True, "live": True, "simulation": False, "message": result.message}


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
    user: Annotated[User, Depends(get_current_admin_writer)],
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
    user: Annotated[User, Depends(get_current_admin_writer)],
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


class TerritoryResearchIn(BaseModel):
    territory_id: UUID
    category: str = "commercial_surface"
    places_query: str | None = None


@router.post("/research/territory")
async def territory_research(
    body: TerritoryResearchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    result = await run_territory_research(
        db,
        territory_id=body.territory_id,
        category=body.category,
        places_query=body.places_query or "",
    )
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.territory_research", entity_id=None)
    await db.commit()
    return result


@router.post("/emergency-pause")
async def emergency_pause(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    policy.emergency_pause_all = True
    platforms = await emergency_pause_connected_platforms()
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.emergency_pause", entity_id=policy.id)
    await db.commit()
    return {"policy": _policy_dict(policy), "platforms": platforms}


@router.post("/outreach/{message_id}/send-approved")
async def send_outreach(
    message_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    msg = await db.get(OutreachMessage, message_id)
    if msg is None:
        raise HTTPException(404)
    prospect = await db.get(CommercialProspect, msg.prospect_id)
    if prospect is None:
        raise HTTPException(404)
    msg.status = OutreachMessageStatus.APPROVED
    msg.approved_by = str(user.id)
    result = await approve_and_send(db, msg, prospect)
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="marketing.outreach_send", entity_id=msg.id)
    await db.commit()
    if not result.get("ok"):
        raise HTTPException(400, result.get("message"))
    return result


class AttributionIn(BaseModel):
    source: str
    medium: str = "unknown"
    content: str | None = None
    utm_campaign: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    campaign_id: UUID | None = None
    flyer_campaign_id: UUID | None = None


@router.post("/attribution/track")
@limiter.limit("30/minute")
async def track_attribution(
    request: Request,
    body: AttributionIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    db.add(
        AttributionEvent(
            source=body.utm_source or body.source,
            medium=body.utm_medium or body.medium,
            content=body.utm_content or body.content,
            utm_campaign=body.utm_campaign,
            utm_source=body.utm_source,
            utm_medium=body.utm_medium,
            utm_content=body.utm_content,
            utm_term=body.utm_term,
            campaign_id=body.campaign_id,
            flyer_campaign_id=body.flyer_campaign_id,
        )
    )
    await db.commit()
    return {"status": "recorded"}