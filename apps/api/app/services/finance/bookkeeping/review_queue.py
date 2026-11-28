from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.finance import BankTransaction, Expense, ExpenseCategory, SyncSource, Receipt
from app.services.finance.bookkeeping.categorizer import (
    AUTO_APPLY_CONFIDENCE,
    CategorisationSuggestion,
    flag_possible_duplicates,
    suggest_for_description,
)


async def create_review_for_transaction(
    db: AsyncSession,
    txn: BankTransaction,
    *,
    allow_auto_apply: bool = False,
) -> BookkeepingReviewItem | None:
    await db.refresh(txn, with_for_update=True)
    if txn.amount_gbp >= 0 or txn.is_reconciled or txn.review_item_id or txn.matched_expense_id or txn.is_duplicate:
        return None

    suggestion = suggest_for_description(txn.description, txn.amount_gbp)
    dup = await flag_possible_duplicates(db, txn)
    suggestion = CategorisationSuggestion(
        category=suggestion.category,
        confidence=suggestion.confidence - (15 if dup else 0),
        explanation=suggestion.explanation + (" Possible duplicate date/amount." if dup else ""),
        is_personal=suggestion.is_personal,
        receipt_required=suggestion.receipt_required,
        vat_likely=suggestion.vat_likely,
        possible_duplicate=dup,
    )

    status = ReviewItemStatus.PENDING
    if (
        allow_auto_apply
        and suggestion.confidence >= AUTO_APPLY_CONFIDENCE
        and not suggestion.is_personal
        and not dup
        and not suggestion.receipt_required
        and not txn.freeagent_explanation_url
        and txn.amount_gbp < 0
    ):
        status = ReviewItemStatus.AUTO_APPLIED
        await _apply_expense_from_suggestion(db, txn, suggestion)

    item = BookkeepingReviewItem(
        bank_transaction_id=txn.id,
        suggested_category=suggestion.category,
        confidence_score=suggestion.confidence,
        plain_explanation=suggestion.explanation,
        status=status,
        is_personal_expenditure=suggestion.is_personal,
        receipt_required=suggestion.receipt_required,
        vat_likely=suggestion.vat_likely,
        possible_duplicate=suggestion.possible_duplicate,
        context_json={"description": txn.description[:200]},
    )
    if status == ReviewItemStatus.AUTO_APPLIED:
        item.resolved_at = datetime.now(UTC)
        item.resolved_by = "system:auto"

    db.add(item)
    await db.flush()
    txn.suggested_category = suggestion.category
    txn.categorisation_confidence = suggestion.confidence
    txn.review_item_id = item.id
    return item


async def _apply_expense_from_suggestion(
    db: AsyncSession, txn: BankTransaction, suggestion: CategorisationSuggestion
) -> Expense:
    amount = abs(txn.amount_gbp)
    exp = Expense(
        description=txn.description[:255],
        category=suggestion.category,
        amount_gbp=amount,
        expense_date=txn.transacted_at,
        source=txn.source,
        receipt_id=None,
    )
    db.add(exp)
    await db.flush()
    txn.matched_expense_id = exp.id
    return exp


async def categorize_uncategorized_transactions(db: AsyncSession, limit: int = 200) -> dict:
    result = await db.execute(
        select(BankTransaction)
        .where(
            BankTransaction.amount_gbp < 0,
            BankTransaction.review_item_id.is_(None),
            BankTransaction.is_reconciled.is_(False),
        )
        .order_by(BankTransaction.transacted_at.desc())
        .limit(limit)
    )
    txns = list(result.scalars().all())
    created = 0
    auto = 0
    for txn in txns:
        item = await create_review_for_transaction(db, txn)
        if item:
            created += 1
            if item.status == ReviewItemStatus.AUTO_APPLIED:
                auto += 1
    return {"reviewed": created, "auto_applied": auto, "queued": created - auto}


async def approve_review_item(
    db: AsyncSession, item_id, actor: str, category: ExpenseCategory | None = None
) -> BookkeepingReviewItem:
    initial = await db.get(BookkeepingReviewItem, item_id)
    if initial and initial.bank_transaction_id:
        await db.get(BankTransaction, initial.bank_transaction_id, with_for_update=True)
    item = await db.get(BookkeepingReviewItem, item_id, with_for_update=True, populate_existing=True)
    if item is None:
        raise ValueError("Review item not found")
    if item.status in (ReviewItemStatus.APPROVED, ReviewItemStatus.AUTO_APPLIED):
        return item

    if item.status != ReviewItemStatus.PENDING:
        raise ValueError("Only pending reviews can be approved")
    if item.is_personal_expenditure or item.possible_duplicate:
        raise ValueError("Resolve personal or duplicate classification before approving an expense")
    cat = category or item.suggested_category or ExpenseCategory.OTHER
    if not item.bank_transaction_id:
        raise ValueError("Receipt-only review requires a verified accounting route before approval")
    if item.bank_transaction_id:
        txn = await db.get(BankTransaction, item.bank_transaction_id, with_for_update=True)
        if txn is None or txn.amount_gbp >= 0 or txn.matched_invoice_id:
            raise ValueError("Only outgoing bank transactions can be approved as expenses")
        if item.receipt_required and not item.receipt_id:
            raise ValueError("Attach and verify the required receipt before approving")
        receipt = None
        if item.receipt_id:
            receipt = await db.get(Receipt, item.receipt_id, with_for_update=True)
            if not receipt or receipt.matched_bank_transaction_id != txn.id or receipt.processing_status != "matched" or receipt.extracted_total_gbp != -txn.amount_gbp:
                raise ValueError("Confirm the receipt match before approving")
        if txn.source == SyncSource.FREEAGENT:
            raise ValueError("Approve accounting entries in FreeAgent and sync")
        if txn and (txn.is_duplicate or txn.is_reconciled or txn.freeagent_explanation_url):
            raise ValueError("Transaction requires reconciliation, not a new expense")
        if txn and txn.amount_gbp < 0 and not txn.matched_expense_id:
            expense = await _apply_expense_from_suggestion(
                db,
                txn,
                CategorisationSuggestion(
                    category=cat,
                    confidence=100,
                    explanation="Owner approved",
                    is_personal=item.is_personal_expenditure,
                    receipt_required=item.receipt_required,
                    vat_likely=item.vat_likely,
                    possible_duplicate=item.possible_duplicate,
                ),
            )
            if receipt:
                expense.receipt_id = receipt.id
    item.status = ReviewItemStatus.APPROVED
    item.resolved_at = datetime.now(UTC)
    item.resolved_by = actor
    item.suggested_category = cat
    return item


async def reject_review_item(db: AsyncSession, item_id, actor: str) -> BookkeepingReviewItem:
    item = await db.get(BookkeepingReviewItem, item_id, with_for_update=True)
    if item is None:
        raise ValueError("Review item not found")
    if item.status == ReviewItemStatus.REJECTED:
        return item
    if item.status != ReviewItemStatus.PENDING:
        raise ValueError("Only pending reviews can be rejected")
    item.status = ReviewItemStatus.REJECTED
    item.resolved_at = datetime.now(UTC)
    item.resolved_by = actor
    return item


async def list_pending_reviews(db: AsyncSession, limit: int = 100) -> list[BookkeepingReviewItem]:
    result = await db.execute(
        select(BookkeepingReviewItem)
        .where(BookkeepingReviewItem.status == ReviewItemStatus.PENDING)
        .order_by(BookkeepingReviewItem.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())