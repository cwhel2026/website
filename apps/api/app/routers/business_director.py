from typing import Annotated
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.agents import AgentProfile
from app.models.user import User
from app.services.business_director import complete_task, list_open_tasks, run_business_director_scan, director_signals, director_target_review
from sqlalchemy import select

router = APIRouter(prefix="/business-director", tags=["business-director"])


@router.post("/scan")
async def scan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    agent = await db.execute(select(AgentProfile).where(AgentProfile.slug == "business_director"))
    profile = agent.scalar_one_or_none()
    if not profile or profile.is_paused or profile.emergency_stop:
        raise HTTPException(503, "Business Director paused")
    tasks = await run_business_director_scan(db)
    await db.commit()
    return {
        "tasks_created": len(tasks),
        "tasks": [
            {"id": str(t.id), "title": t.title, "agent_slug": t.agent_slug, "priority": t.priority}
            for t in tasks
        ],
    }


@router.get("/tasks")
async def tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = await list_open_tasks(db)
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "agent_slug": t.agent_slug,
            "action_key": t.action_key,
            "status": t.status.value,
            "priority": t.priority,
        }
        for t in rows
    ]


@router.post("/tasks/{task_id}/complete")
async def task_complete(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    t = await complete_task(db, task_id)
    if t is None:
        raise HTTPException(404)
    await db.commit()
    return {"id": str(t.id), "status": t.status.value}

@router.get("/overview")
async def overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    profiles = (await db.execute(select(AgentProfile).order_by(AgentProfile.slug))).scalars().all()
    return {"signals": await director_signals(db), "agents": [{"slug": p.slug, "name": p.name, "mode": p.operating_mode.value, "paused": p.is_paused, "emergency_stop": p.emergency_stop} for p in profiles], "external_actions_enabled": False, "basis": "local_database"}


@router.get("/target-review")
async def target_review(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    monthly_target: Decimal = Query(gt=0, le=10000000),
) -> dict:
    return await director_target_review(db, monthly_target)
