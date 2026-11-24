from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.agents import AgentProfile
from app.models.user import User
from app.services.business_director import complete_task, list_open_tasks, run_business_director_scan
from sqlalchemy import select

router = APIRouter(prefix="/business-director", tags=["business-director"])


@router.post("/scan")
async def scan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    agent = await db.execute(select(AgentProfile).where(AgentProfile.slug == "business_director"))
    profile = agent.scalar_one_or_none()
    if profile and (profile.is_paused or profile.emergency_stop):
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
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    t = await complete_task(db, task_id)
    if t is None:
        raise HTTPException(404)
    await db.commit()
    return {"id": str(t.id), "status": t.status.value}