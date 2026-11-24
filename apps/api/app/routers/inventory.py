from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.inventory import StockItem
from app.models.user import User
from app.services.materials_forecast import forecast_coating_for_days, low_stock_alerts

router = APIRouter(prefix="/inventory", tags=["inventory"])


class StockAdjust(BaseModel):
    quantity_delta: Decimal


@router.get("/items")
async def list_stock(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(select(StockItem).where(StockItem.is_active.is_(True)))
    return [
        {
            "sku": s.sku,
            "name": s.name,
            "category": s.category.value,
            "quantity_on_hand": float(s.quantity_on_hand),
            "reorder_level": float(s.reorder_level),
            "unit": s.unit,
        }
        for s in result.scalars().all()
    ]


@router.patch("/items/{item_id}")
async def adjust_stock(
    item_id: UUID,
    body: StockAdjust,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    item = await db.get(StockItem, item_id)
    if item is None:
        raise HTTPException(404)
    item.quantity_on_hand += body.quantity_delta
    await db.commit()
    return {"sku": item.sku, "quantity_on_hand": float(item.quantity_on_hand)}


@router.get("/forecast")
async def materials_forecast(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 7,
) -> dict:
    needs = await forecast_coating_for_days(db, days)
    alerts = await low_stock_alerts(db)
    return {
        "days": days,
        "needs": [n.__dict__ for n in needs],
        "low_stock": alerts,
    }