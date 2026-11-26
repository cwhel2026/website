from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.marketing.attribution_journey import marketing_funnel_attribution
from app.services.marketing.budget_controls import emergency_pause_connected_platforms, get_or_create_budget_policy
from app.services.marketing.director_proactive import list_director_history, run_daily_director_cycle
from app.services.marketing.experiments_engine import evaluate_experiment, list_experiments
from app.services.marketing.launch_readiness import assess_launch_readiness
from app.services.marketing.prospect_categories import PROSPECT_VERTICALS, TERRITORY_AREAS

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
    _: Annotated[User, Depends(get_current_admin)],
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
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    from uuid import UUID

    return await evaluate_experiment(db, UUID(experiment_id))


@router.post("/pause-all-advertising")
async def pause_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    policy = await get_or_create_budget_policy(db)
    policy.emergency_pause_all = True
    platforms = await emergency_pause_connected_platforms()
    await db.commit()
    return {"emergency_pause_all": True, "platforms": platforms}