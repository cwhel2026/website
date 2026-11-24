from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.analytics_service import build_analytics_snapshot, regional_analytics
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 30,
) -> dict:
    snap = await build_analytics_snapshot(db, days)
    return snap.__dict__


@router.get("/regional")
async def regional(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await regional_analytics(db)