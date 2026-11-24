from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.approvals import ApprovalRequest, ApprovalStatus, ApprovalType
from app.models.communications import (
    MessageCategory,
    MessageChannel,
    MessageTemplate,
    OutboundMessage,
    OutboundStatus,
)
from app.models.user import User
from app.services.audit import record_audit

router = APIRouter(prefix="/communications", tags=["communications"])


class TemplateOut(BaseModel):
    slug: str
    name: str
    channel: MessageChannel
    category: MessageCategory

    class Config:
        from_attributes = True


class QueueMessageIn(BaseModel):
    template_slug: str
    recipient: EmailStr
    customer_id: UUID | None = None
    context: dict[str, str] | None = None
    send_immediately: bool = False


class OutboundOut(BaseModel):
    id: UUID
    status: OutboundStatus
    channel: MessageChannel
    recipient: str

    class Config:
        from_attributes = True


@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(db: Annotated[AsyncSession, Depends(get_db)]) -> list[MessageTemplate]:
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.is_active.is_(True)).order_by(MessageTemplate.slug)
    )
    return list(result.scalars().all())


@router.post("/queue", response_model=OutboundOut)
async def queue_message(
    body: QueueMessageIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> OutboundMessage:
    tpl_result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.slug == body.template_slug)
    )
    tpl = tpl_result.scalar_one_or_none()
    if tpl is None:
        raise HTTPException(404, "Template not found")

    text = tpl.body_template
    if body.context:
        for key, val in body.context.items():
            text = text.replace("{{" + key + "}}", val)

    status = OutboundStatus.PENDING_APPROVAL
    if body.send_immediately:
        status = OutboundStatus.QUEUED  # still not sent without provider

    msg = OutboundMessage(
        customer_id=body.customer_id,
        template_slug=tpl.slug,
        channel=tpl.channel,
        category=tpl.category,
        status=status,
        recipient=body.recipient,
        subject=tpl.subject_template,
        body=text,
    )
    db.add(msg)
    await db.flush()

    if status == OutboundStatus.PENDING_APPROVAL:
        db.add(
            ApprovalRequest(
                approval_type=ApprovalType.CUSTOMER_MESSAGE,
                title=f"Send message: {tpl.name}",
                summary=text[:500],
                entity_type="outbound_message",
                entity_id=msg.id,
                requested_by="communications",
            )
        )

    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="communications.queue",
        entity_id=msg.id,
    )
    await db.commit()
    await db.refresh(msg)
    return msg