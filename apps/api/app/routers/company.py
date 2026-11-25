from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.company import OnboardingTaskStatus
from app.models.user import User
from app.schemas.company import (
    CompanyOnboardingSummary,
    CompanyProfileIn,
    CompanyProfileOut,
    OnboardingTaskOut,
)
from app.services.company.onboarding import get_or_create_profile, refresh_task_statuses

router = APIRouter(prefix="/company", tags=["company"])


def _completion_pct(tasks: list) -> int:
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.status == OnboardingTaskStatus.COMPLETED)
    return int((done / len(tasks)) * 100)


@router.get("/profile", response_model=CompanyOnboardingSummary)
async def get_company_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> CompanyOnboardingSummary:
    profile = await get_or_create_profile(db)
    await db.refresh(profile)
    from sqlalchemy import select
    from app.models.company import CompanyOnboardingTask

    result = await db.execute(
        select(CompanyOnboardingTask).order_by(CompanyOnboardingTask.sort_order)
    )
    task_rows = list(result.scalars().all())
    next_actions = [
        t.title
        for t in task_rows
        if t.status
        in (
            OnboardingTaskStatus.INFO_REQUIRED,
            OnboardingTaskStatus.PREPARATION_REQUIRED,
            OnboardingTaskStatus.UPCOMING,
        )
    ][:5]
    out = CompanyProfileOut.model_validate(profile)
    out.tasks = [OnboardingTaskOut.model_validate(t) for t in task_rows]
    await db.commit()
    return CompanyOnboardingSummary(
        profile=out,
        completion_pct=_completion_pct(task_rows),
        next_actions=next_actions,
    )


@router.put("/profile", response_model=CompanyProfileOut)
async def update_company_profile(
    body: CompanyProfileIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> CompanyProfileOut:
    profile = await get_or_create_profile(db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await refresh_task_statuses(db, profile)
    from sqlalchemy import select
    from app.models.company import CompanyOnboardingTask

    result = await db.execute(
        select(CompanyOnboardingTask).order_by(CompanyOnboardingTask.sort_order)
    )
    task_rows = list(result.scalars().all())
    await db.commit()
    out = CompanyProfileOut.model_validate(profile)
    out.tasks = [OnboardingTaskOut.model_validate(t) for t in task_rows]
    return out


@router.post("/onboarding/complete")
async def mark_onboarding_complete(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, str]:
    profile = await get_or_create_profile(db)
    if not profile.companies_house_number:
        raise HTTPException(400, "Add your Companies House number before completing onboarding.")
    from datetime import UTC, datetime

    profile.onboarding_completed_at = datetime.now(UTC)
    await db.commit()
    return {"status": "ok"}