from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_accountant_or_admin
from app.database import get_db
from app.models.user import User
from app.services.compliance.engine import upcoming_reminders
from app.services.finance.exports import (
    export_bank_transactions_csv,
    export_expenses_csv,
    export_invoices_csv,
    year_end_pack_metadata,
)
from app.services.finance.bookkeeping.review_queue import list_pending_reviews
from app.services.finance.tax_reserves import compute_tax_reserves

router = APIRouter(prefix="/finance/accountant", tags=["accountant"])


@router.get("/review-queue")
async def accountant_review_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
) -> list[dict]:
    items = await list_pending_reviews(db, limit=200)
    return [
        {
            "id": str(i.id),
            "explanation": i.plain_explanation,
            "confidence": i.confidence_score,
            "category": i.suggested_category.value if i.suggested_category else None,
        }
        for i in items
    ]


@router.get("/tax-summary")
async def accountant_tax_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
) -> dict:
    reserves = await compute_tax_reserves(db)
    compliance = await upcoming_reminders(db, within_days=180)
    await db.commit()
    return {"reserves": reserves, "compliance": compliance, "year_end_pack": year_end_pack_metadata()}


@router.get("/export/invoices.csv")
async def export_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
) -> Response:
    csv_text = await export_invoices_csv(db)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"},
    )


@router.get("/export/expenses.csv")
async def export_expenses(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
) -> Response:
    csv_text = await export_expenses_csv(db)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


@router.get("/export/bank.csv")
async def export_bank(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
) -> Response:
    csv_text = await export_bank_transactions_csv(db)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bank_transactions.csv"},
    )