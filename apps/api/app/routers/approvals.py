from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.approvals import ApprovalRequest, ApprovalStatus, ApprovalType
from app.models.quotation import Quotation, QuotationStatus
from app.models.user import User
from app.models.marketing import CampaignStatus, RegionalCampaign
from app.services.audit import record_audit

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalOut(BaseModel):
    id: UUID
    approval_type: ApprovalType
    status: ApprovalStatus
    title: str
    summary: str | None
    entity_type: str | None
    entity_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class DecideIn(BaseModel):
    note: str | None = None


@router.get("", response_model=list[ApprovalOut])
async def list_approvals(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    status: ApprovalStatus | None = ApprovalStatus.PENDING,
) -> list[ApprovalRequest]:
    q = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).limit(100)
    if status:
        q = q.where(ApprovalRequest.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(
    approval_id: UUID,
    body: DecideIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> ApprovalRequest:
    req = await db.get(ApprovalRequest, approval_id, with_for_update=True)
    if req is None:
        raise HTTPException(404, "Not found")
    if req.status != ApprovalStatus.PENDING:
        raise HTTPException(400, "Already decided")
    req.status = ApprovalStatus.APPROVED
    req.decided_by_user_id = user.id
    req.decision_note = body.note
    req.decided_at = datetime.now(UTC)
    if req.approval_type == ApprovalType.QUOTATION and req.entity_id:
        quotation = await db.get(Quotation, req.entity_id)
        if quotation:
            quotation.status = QuotationStatus.SENT
            quotation.requires_approval = False
    if req.approval_type == ApprovalType.AD_SPEND and req.entity_type == "regional_campaign" and req.entity_id:
        campaign = await db.get(RegionalCampaign, req.entity_id)
        if campaign and campaign.status == CampaignStatus.PENDING_APPROVAL:
            campaign.status = CampaignStatus.APPROVED
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="approval.approve",
        entity_type=req.entity_type,
        entity_id=req.entity_id,
    )
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(
    approval_id: UUID,
    body: DecideIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> ApprovalRequest:
    req = await db.get(ApprovalRequest, approval_id, with_for_update=True)
    if req is None:
        raise HTTPException(404, "Not found")
    if req.status != ApprovalStatus.PENDING:
        raise HTTPException(400, "Already decided")
    req.status = ApprovalStatus.REJECTED
    req.decided_by_user_id = user.id
    req.decision_note = body.note
    req.decided_at = datetime.now(UTC)
    if req.approval_type == ApprovalType.QUOTATION and req.entity_id:
        quotation = await db.get(Quotation, req.entity_id)
        if quotation:
            quotation.status = QuotationStatus.REJECTED
    if req.approval_type == ApprovalType.AD_SPEND and req.entity_type == "regional_campaign" and req.entity_id:
        campaign = await db.get(RegionalCampaign, req.entity_id)
        if campaign and campaign.status == CampaignStatus.PENDING_APPROVAL:
            campaign.status = CampaignStatus.DRAFT
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="approval.reject", entity_id=req.entity_id)
    await db.commit()
    await db.refresh(req)
    return req