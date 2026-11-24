from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import ApprovalRequest, ApprovalStatus, ApprovalType
from app.models.quotation import Quotation


async def ensure_quotation_approval(db: AsyncSession, quotation: Quotation) -> ApprovalRequest | None:
    if not quotation.requires_approval:
        return None
    existing = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.entity_type == "quotation",
            ApprovalRequest.entity_id == quotation.id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none():
        return None
    req = ApprovalRequest(
        approval_type=ApprovalType.QUOTATION,
        title=f"Quotation {quotation.reference} requires approval",
        summary=(
            f"Total inc VAT £{quotation.total_inc_vat_gbp}; "
            f"meets_minimum_margin={quotation.meets_minimum_margin}"
        ),
        entity_type="quotation",
        entity_id=quotation.id,
        requested_by="quotation_engine",
    )
    db.add(req)
    await db.flush()
    return req