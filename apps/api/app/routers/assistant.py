import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.agents import AgentProfile
from app.models.assistant_chat import AssistantConversation, AssistantMessage
from app.models.user import User
from app.services.ai.orchestrator import answer_question
from app.services.audit import record_audit

router = APIRouter(prefix="/assistant", tags=["assistant"])
settings = get_settings()


class ChatIn(BaseModel):
    message: str
    conversation_id: UUID | None = None


class ChatOut(BaseModel):
    conversation_id: UUID
    reply: str
    tool_data: dict
    provider: str


@router.post("/chat", response_model=ChatOut)
async def chat(
    body: ChatIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> ChatOut:
    paused = await db.execute(
        select(AgentProfile).where(AgentProfile.slug == "personal_assistant")
    )
    profile = paused.scalar_one_or_none()
    if profile and (profile.is_paused or profile.emergency_stop or settings.global_emergency_stop):
        raise HTTPException(503, "Personal assistant is paused")

    if body.conversation_id:
        conv_id = body.conversation_id
    else:
        conv = AssistantConversation(user_id=user.id)
        db.add(conv)
        await db.flush()
        conv_id = conv.id

    db.add(
        AssistantMessage(conversation_id=conv_id, role="user", content=body.message)
    )

    reply, tool_data, provider = await answer_question(db, body.message)
    db.add(
        AssistantMessage(
            conversation_id=conv_id,
            role="assistant",
            content=reply,
            tool_calls_json=json.dumps(tool_data),
        )
    )
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="assistant.chat",
        detail={"conversation_id": str(conv_id), "tools": list(tool_data.keys())},
    )
    await db.commit()
    return ChatOut(
        conversation_id=conv_id,
        reply=reply,
        tool_data=tool_data,
        provider=provider,
    )