import hmac
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.finance import ExpenseCategory, BankTransaction, Receipt
from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
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
    user: Annotated[User, Depends(get_current_admin_writer)],
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
    if not expected or not ingest_key or not hmac.compare_digest(ingest_key, expected):
        raise HTTPException(401, "Invalid ingest key")
    try:
        receipt, detail = await ingest_telegram_receipt(
            db, body.file_id, mime_hint=body.mime_type or "image/jpeg"
        )
    except Exception as exc:
        await db.rollback()
        raise HTTPException(502, "Receipt ingest failed") from exc
    await db.commit()
    return {
        "receipt_id": str(receipt.id),
        "reply": summarise_receipt_reply(receipt, detail),
        "status": receipt.processing_status,
    }

class ReceiptMatchDecision(BaseModel):
    transaction_id: UUID
    confirmed: bool = False


@router.post("/receipts/{receipt_id}/confirm-match")
async def confirm_receipt_match(
    receipt_id: UUID,
    body: ReceiptMatchDecision,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    if not body.confirmed:
        raise HTTPException(422, "Explicit receipt match confirmation required")
    txn = await db.get(BankTransaction, body.transaction_id, with_for_update=True)
    receipt = await db.get(Receipt, receipt_id, with_for_update=True)
    if not txn or not receipt:
        raise HTTPException(404, "Receipt or bank transaction not found")
    if txn.is_duplicate or txn.amount_gbp >= 0 or txn.matched_invoice_id:
        raise HTTPException(409, "Ineligible outgoing transaction")
    if not receipt.extracted_date or receipt.extracted_total_gbp is None or receipt.extracted_total_gbp != -txn.amount_gbp:
        raise HTTPException(409, "Receipt amount and date must be verified")
    if abs((receipt.extracted_date - txn.transacted_at).days) > 7:
        raise HTTPException(409, "Receipt and bank dates differ by more than seven days")
    if receipt.freeagent_expense_url or receipt.freeagent_attach_status in ("attached", "expense_created", "posting", "uncertain", "failed"):
        raise HTTPException(409, "Existing external accounting activity requires manual review")
    other = await db.scalar(select(Receipt.id).where(Receipt.matched_bank_transaction_id == txn.id, Receipt.id != receipt.id).limit(1))
    if other:
        raise HTTPException(409, "Another receipt already references this transaction")
    if receipt.matched_bank_transaction_id and receipt.matched_bank_transaction_id != txn.id:
        raise HTTPException(409, "Resolve existing receipt match before changing it")
    if txn.review_item_id:
        item = await db.get(BookkeepingReviewItem, txn.review_item_id, with_for_update=True)
        if item and item.status == ReviewItemStatus.PENDING:
            if item.receipt_id and item.receipt_id != receipt.id:
                raise HTTPException(409, "Review already references another receipt")
            item.receipt_id = receipt.id
    receipt.matched_bank_transaction_id = txn.id
    receipt.processing_status = "matched"
    await record_audit(db, actor_type="user", actor_id=str(user.id),
        action="receipt.confirm_match", entity_id=receipt.id,
        detail={"transaction_id": str(txn.id)})
    await db.commit()
    return {"status": "matched", "external_posted": False}


@router.get("/receipts/match-review")
async def receipt_match_review(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = await db.execute(select(Receipt, BankTransaction).join(
        BankTransaction, Receipt.matched_bank_transaction_id == BankTransaction.id
    ).where(Receipt.processing_status == "needs_review",
        BankTransaction.is_duplicate.is_(False),
        BankTransaction.amount_gbp < 0
    ).order_by(BankTransaction.transacted_at.desc()).limit(100))
    return [{
        "receipt_id": str(receipt.id), "transaction_id": str(txn.id),
        "merchant": receipt.extracted_merchant, "receipt_total": str(receipt.extracted_total_gbp) if receipt.extracted_total_gbp is not None else None,
        "receipt_date": receipt.extracted_date.isoformat() if receipt.extracted_date else None,
        "bank_description": txn.description, "bank_amount": str(txn.amount_gbp),
        "bank_date": txn.transacted_at.isoformat(),
        "eligible": receipt.extracted_total_gbp == -txn.amount_gbp and receipt.extracted_date is not None and abs((receipt.extracted_date - txn.transacted_at).days) <= 7,
    } for receipt, txn in rows.all()]
