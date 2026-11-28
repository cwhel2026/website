from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.booking_payment import BookingDeposit
from app.models.user import User
from app.services.audit import record_audit
from app.services.payments.booking import draft_deposit

router = APIRouter(prefix="/booking-payments", tags=["booking-payments"])
DB = Annotated[AsyncSession, Depends(get_db)]


class DepositRequest(BaseModel):
    percentage: Decimal = Field(default=Decimal("10"), gt=0, le=100, decimal_places=2)


def serialize(row: BookingDeposit) -> dict:
    return {"id": str(row.id), "job_id": str(row.job_id),
            "invoice_id": str(row.invoice_id) if row.invoice_id else None,
            "total_pence": row.total_pence, "amount_pence": row.amount_pence,
            "status": row.status, "payment_url": row.payment_url}


@router.post("/jobs/{job_id}/deposit")
async def create_deposit(job_id: UUID, body: DepositRequest, db: DB,
                         user: Annotated[User, Depends(get_current_admin_writer)]) -> dict:
    try:
        row = await draft_deposit(db, job_id, body.percentage)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(409, str(exc)) from None
    await record_audit(db, actor_type="user", actor_id=str(user.id),
                       action="booking.deposit_draft", entity_id=row.id)
    result = serialize(row)
    await db.commit()
    return result


@router.get("/jobs/{job_id}/deposit")
async def get_deposit(job_id: UUID, db: DB,
                      _: Annotated[User, Depends(get_current_admin)]) -> dict:
    row = await db.scalar(select(BookingDeposit).where(BookingDeposit.job_id == job_id))
    if not row:
        raise HTTPException(404, "Booking deposit not found")
    return serialize(row)
