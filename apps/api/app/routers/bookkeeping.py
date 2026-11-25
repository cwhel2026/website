from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.finance import ExpenseCategory
from app.models.user import User
from app.services.audit import record_audit
from app.services.finance.bookkeeping.review_queue import (
    approve_review_item,
    categorize_uncategorized_transactions,
    list_pending_reviews,
    reject_review_item,
)
from app.services.finance.bookkeeping.receipt_processor import (
    ingest_telegram_receipt,
    summarise_receipt_reply,
)
from app.services.finance.receipt_accounting import push_receipt_to_freeagent
router = APIRouter(prefix="/finance/bookkeeping", tags=["bookkeeping"])


class ReviewDecision(BaseModel):
    category: ExpenseCategory | None = None


@router.post("/categorize/run")
async def run_categorization(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await categorize_uncategorized_transactions(db)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="bookkeeping.categorize",
        detail=result,
    )
    await db.commit()
    return result


@router.get("/review-queue")
async def review_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    items = await list_pending_reviews(db)
    return [
        {
            "id": str(i.id),
            "confidence": i.confidence_score,
            "category": i.suggested_category.value if i.suggested_category else None,
            "explanation": i.plain_explanation,
            "bank_transaction_id": str(i.bank_transaction_id) if i.bank_transaction_id else None,
            "receipt_id": str(i.receipt_id) if i.receipt_id else None,
            "personal": i.is_personal_expenditure,
            "receipt_required": i.receipt_required,
            "duplicate": i.possible_duplicate,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


@router.post("/receipts/{receipt_id}/attach-freeagent")
async def attach_receipt(
    receipt_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    from app.models.finance import Receipt

    receipt = await db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(404, "Receipt not found")
    result = await push_receipt_to_freeagent(db, receipt, approved=True)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="receipt.attach_freeagent",
        entity_id=receipt_id,
        detail=result,
    )
    await db.commit()
    return result


@router.post("/review-queue/{item_id}/approve")
async def approve_item(
    item_id: UUID,
    body: ReviewDecision,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict[str, str]:
    try:
        item = await approve_review_item(db, item_id, str(user.id), body.category)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if item.receipt_id:
        from app.models.finance import Receipt

        receipt = await db.get(Receipt, item.receipt_id)
        if receipt:
            await push_receipt_to_freeagent(db, receipt, approved=True)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="bookkeeping.approve",
        entity_id=item_id,
    )
    await db.commit()
    return {"status": "approved"}


@router.post("/review-queue/{item_id}/reject")
async def reject_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict[str, str]:
    try:
        await reject_review_item(db, item_id, str(user.id))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.commit()
    return {"status": "rejected"}


class TelegramReceiptIn(BaseModel):
    file_id: str
    mime_type: str | None = "image/jpeg"


@router.post("/receipts/telegram")
async def telegram_receipt_ingest(
    body: TelegramReceiptIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    ingest_key: Annotated[str | None, Header(alias="X-Finance-Telegram-Ingest-Key")] = None,
) -> dict:
    """Internal ingest from Telegram webhook (FastAPI or trusted Next forward)."""
    from app.config import get_settings

    settings = get_settings()
    expected = (settings.finance_telegram_ingest_key or "").strip()
    if not expected or ingest_key != expected:
        raise HTTPException(401, "Invalid ingest key")
    try:
        receipt, detail = await ingest_telegram_receipt(
            db, body.file_id, mime_hint=body.mime_type or "image/jpeg"
        )
    except Exception as exc:
        await db.rollback()
        raise HTTPException(502, f"Receipt ingest failed: {exc}") from exc
    await db.commit()
    return {
        "receipt_id": str(receipt.id),
        "reply": summarise_receipt_reply(receipt, detail),
        "status": receipt.processing_status,
    }