from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookkeeping import BookkeepingReviewItem
from app.models.finance import BankTransaction
from app.models.remuneration import DirectorsLoanEntry, DirectorsLoanEntryKind


async def sync_directors_loan_from_reviews(db: AsyncSession) -> dict:
    """Create loan entries for transactions flagged personal — does not auto-correct books."""
    result = await db.execute(
        select(BookkeepingReviewItem).where(
            BookkeepingReviewItem.is_personal_expenditure.is_(True),
            BookkeepingReviewItem.bank_transaction_id.is_not(None),
        )
    )
    created = 0
    for item in result.scalars().all():
        existing = await db.execute(
            select(DirectorsLoanEntry).where(DirectorsLoanEntry.bank_transaction_id == item.bank_transaction_id)
        )
        if existing.scalar_one_or_none():
            continue
        txn = await db.get(BankTransaction, item.bank_transaction_id)
        if not txn or txn.amount_gbp >= 0:
            continue
        entry = DirectorsLoanEntry(
            kind=DirectorsLoanEntryKind.WITHDRAWAL,
            amount_gbp=abs(txn.amount_gbp),
            transacted_at=txn.transacted_at,
            note=txn.description[:255],
            bank_transaction_id=txn.id,
        )
        db.add(entry)
        created += 1
    await db.flush()
    balance = await loan_balance(db)
    return {"entries_added": created, "balance_gbp": balance["balance_gbp"], **balance}


async def loan_balance(db: AsyncSession) -> dict:
    result = await db.execute(select(DirectorsLoanEntry))
    balance = Decimal("0")
    for row in result.scalars().all():
        if row.kind in (DirectorsLoanEntryKind.WITHDRAWAL,):
            balance += row.amount_gbp
        elif row.kind in (DirectorsLoanEntryKind.INTRODUCTION, DirectorsLoanEntryKind.REPAYMENT):
            balance -= row.amount_gbp
    return {
        "balance_gbp": float(balance),
        "plain_english": (
            "You owe the company money via the director's loan account — repayment may avoid Section 455 tax."
            if balance > 0
            else "No net director loan balance recorded."
        ),
        "requires_accountant_review": balance > 0,
    }