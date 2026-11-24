from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.agents import AgentActionPermission, AgentProfile, OperatingMode
from app.models.background_job import BackgroundJobRun, JobRunStatus
from app.models.user import User
from app.services.audit import record_audit

router = APIRouter(prefix="/automations", tags=["automations"])
settings = get_settings()


class AgentOut(BaseModel):
    slug: str
    name: str
    operating_mode: OperatingMode
    is_paused: bool
    emergency_stop: bool

    class Config:
        from_attributes = True


class ModeUpdate(BaseModel):
    operating_mode: OperatingMode | None = None
    is_paused: bool | None = None


@router.get("/agents", response_model=list[AgentOut])
async def list_agents(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[AgentProfile]:
    result = await db.execute(select(AgentProfile).order_by(AgentProfile.slug))
    return list(result.scalars().all())


@router.patch("/agents/{slug}", response_model=AgentOut)
async def update_agent(
    slug: str,
    body: ModeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> AgentProfile:
    result = await db.execute(select(AgentProfile).where(AgentProfile.slug == slug))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(404, "Agent not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    await record_audit(
        db, actor_type="user", actor_id=str(user.id), action="agent.update", detail={"slug": slug}
    )
    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/emergency-stop")
async def emergency_stop(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict[str, str]:
    result = await db.execute(select(AgentProfile))
    for agent in result.scalars().all():
        agent.emergency_stop = True
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="emergency_stop")
    await db.commit()
    return {"message": "All agents paused via emergency stop (database flag)"}


TASK_CATALOG = [
    {"task_name": "refresh_weather_hq", "description": "Refresh HQ hourly forecast cache"},
    {"task_name": "appointment_weather_risk", "description": "Re-score upcoming appointments vs live weather"},
    {"task_name": "morning_briefing", "description": "Generate morning briefing payload"},
    {"task_name": "marketing_capacity_snapshot", "description": "Snapshot global marketing capacity"},
]


@router.get("/workers/catalog")
async def worker_catalog(
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    return TASK_CATALOG


@router.get("/workers/runs")
async def worker_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    """Last successful run per task — real rows from background_job_runs."""
    latest: list[dict] = []
    for task in TASK_CATALOG:
        name = task["task_name"]
        result = await db.execute(
            select(BackgroundJobRun)
            .where(BackgroundJobRun.task_name == name)
            .order_by(BackgroundJobRun.created_at.desc())
            .limit(3)
        )
        rows = list(result.scalars().all())
        last_ok = next((r for r in rows if r.status == JobRunStatus.SUCCEEDED), None)
        latest.append(
            {
                "task_name": name,
                "description": task["description"],
                "last_status": rows[0].status.value if rows else "never_run",
                "last_started_at": rows[0].started_at.isoformat() if rows and rows[0].started_at else None,
                "last_finished_at": rows[0].finished_at.isoformat() if rows and rows[0].finished_at else None,
                "last_success_at": last_ok.finished_at.isoformat() if last_ok and last_ok.finished_at else None,
                "recent_error": next(
                    (r.error_message for r in rows if r.status == JobRunStatus.FAILED and r.error_message),
                    None,
                ),
            }
        )
    return {
        "redis_configured": bool(settings.redis_url),
        "catalog": TASK_CATALOG,
        "tasks": latest,
    }


@router.post("/workers/trigger/{task_name}")
async def trigger_worker_task(
    task_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    from app.worker import tasks as worker_tasks

    mapping = {
        "refresh_weather_hq": worker_tasks.refresh_weather_hq,
        "appointment_weather_risk": worker_tasks.appointment_weather_risk,
        "morning_briefing": worker_tasks.morning_briefing,
        "marketing_capacity_snapshot": worker_tasks.marketing_capacity_snapshot,
    }
    task = mapping.get(task_name)
    if task is None:
        raise HTTPException(404, "Unknown task")
    async_result = task.delay()
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="worker.trigger",
        detail={"task": task_name, "celery_id": async_result.id},
    )
    await db.commit()
    return {"message": "Task queued", "task_name": task_name, "celery_id": async_result.id}


@router.get("/permissions", response_model=list[dict])
async def list_permissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(select(AgentActionPermission).order_by(AgentActionPermission.agent_slug))
    return [
        {
            "agent_slug": p.agent_slug,
            "action_key": p.action_key,
            "requires_approval": p.requires_approval,
            "allowed_in_controlled": p.allowed_in_controlled,
        }
        for p in result.scalars().all()
    ]