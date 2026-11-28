from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.marketing_ops import CommercialPipelineStage, CommercialProspect
from app.models.user import User
from app.services.marketing.attribution_journey import marketing_funnel_attribution
from app.services.marketing.brand_profile import brand_json, get_or_create_brand
from app.services.marketing.budget_controls import emergency_pause_connected_platforms, get_or_create_budget_policy
from app.services.marketing.commercial_pipeline import transition_pipeline
from app.services.marketing.competitor_research import list_competitor_findings, research_competitors
from app.services.marketing.director_proactive import list_director_history, run_daily_director_cycle
from app.services.marketing.experiments_engine import evaluate_experiment, list_experiments
from app.services.marketing.google_seo_clients import seo_dashboard_snapshot
from app.services.marketing.launch_planner import generate_launch_plan, latest_launch_plan
from app.services.marketing.launch_readiness import assess_launch_readiness
from app.services.marketing.profitability_full import marketing_profitability_full
from app.services.marketing.prospect_categories import PROSPECT_VERTICALS, TERRITORY_AREAS
from app.services.marketing.website_seo_audit import audit_public_site

router = APIRouter(prefix="/marketing/launch", tags=["marketing-launch"])


@router.get("/readiness")
async def launch_readiness(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return assess_launch_readiness()


@router.get("/verticals")
async def prospect_verticals(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return {"verticals": list(PROSPECT_VERTICALS.keys()), "areas": TERRITORY_AREAS}


@router.post("/director/run")
async def director_run(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
    research: bool = False,
) -> dict:
    result = await run_daily_director_cycle(db, execute_research=research)
    await db.commit()
    return result


@router.get("/director/history")
async def director_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return {"runs": await list_director_history(db)}


@router.get("/attribution-journey")
async def attribution_journey(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 90,
) -> dict:
    return await marketing_funnel_attribution(db, days=days)


@router.get("/experiments")
async def experiments_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return {"experiments": await list_experiments(db)}


@router.post("/experiments/{experiment_id}/evaluate")
async def experiments_eval(
    experiment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    from uuid import UUID

    return await evaluate_experiment(db, UUID(experiment_id))


@router.post("/pause-all-advertising")
async def pause_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    policy.emergency_pause_all = True
    platforms = await emergency_pause_connected_platforms()
    await db.commit()
    return {"emergency_pause_all": True, "platforms": platforms}


@router.get("/brand")
async def get_brand(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await brand_json(db)


class BrandPatchIn(BaseModel):
    tone_of_voice: str | None = None
    tagline: str | None = None
    phone: str | None = None
    service_areas: list[str] | None = None
    approved_claims: list[str] | None = None
    approved_ctas: list[str] | None = None
    photo_permission_policy: str | None = None


@router.patch("/brand")
async def patch_brand(
    body: BrandPatchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    brand = await get_or_create_brand(db)
    if body.tone_of_voice is not None:
        brand.tone_of_voice = body.tone_of_voice
    if body.tagline is not None:
        brand.tagline = body.tagline
    if body.phone is not None:
        brand.phone = body.phone
    if body.service_areas is not None:
        brand.service_areas_json = body.service_areas
    if body.approved_claims is not None:
        brand.approved_claims_json = body.approved_claims
    if body.approved_ctas is not None:
        brand.approved_ctas_json = body.approved_ctas
    if body.photo_permission_policy is not None:
        brand.photo_permission_policy = body.photo_permission_policy
    await db.commit()
    return await brand_json(db)


@router.get("/competitors")
async def competitors_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return {"findings": await list_competitor_findings(db)}


class CompetitorResearchIn(BaseModel):
    area: str = Field(min_length=2)
    territory_code: str | None = None


@router.post("/competitors/research")
async def competitors_research(
    body: CompetitorResearchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    result = await research_competitors(db, area=body.area, territory_code=body.territory_code)
    await db.commit()
    return result


@router.get("/seo")
async def seo_dashboard(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return await seo_dashboard_snapshot()


@router.get("/seo/website-audit")
async def seo_website_audit(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return await audit_public_site()


@router.get("/profitability")
async def profitability(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 90,
) -> dict:
    return await marketing_profitability_full(db, days=days)


class LaunchPlanIn(BaseModel):
    launch_date: date | None = None


@router.post("/launch-plan")
async def create_launch_plan(
    body: LaunchPlanIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    plan = await generate_launch_plan(db, launch_date=body.launch_date)
    await db.commit()
    return plan


@router.get("/launch-plan")
async def get_launch_plan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    plan = await latest_launch_plan(db)
    if plan is None:
        raise HTTPException(404, "No launch plan yet — POST /launch-plan to generate")
    return plan


class PipelineTransitionIn(BaseModel):
    stage: CommercialPipelineStage
    note: str = ""


@router.post("/commercial-prospects/{prospect_id}/pipeline")
async def commercial_pipeline_transition(
    prospect_id: UUID,
    body: PipelineTransitionIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    prospect = await db.get(CommercialProspect, prospect_id)
    if prospect is None:
        raise HTTPException(404, "Prospect not found")
    ok, msg = await transition_pipeline(db, prospect, body.stage, note=body.note)
    if not ok:
        raise HTTPException(400, msg)
    await db.commit()
    return {"ok": True, "pipeline_stage": prospect.pipeline_stage.value, "message": msg}