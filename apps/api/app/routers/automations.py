from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.agents import AgentActionPermission, AgentProfile, OperatingMode
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