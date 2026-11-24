from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
async def list_services(db: Annotated[AsyncSession, Depends(get_db)]) -> list[Service]:
    result = await db.execute(
        select(Service).where(Service.is_active.is_(True)).order_by(Service.sort_order)
    )
    return list(result.scalars().all())


@router.get("/{slug}", response_model=ServiceOut)
async def get_service(slug: str, db: Annotated[AsyncSession, Depends(get_db)]) -> Service:
    result = await db.execute(select(Service).where(Service.slug == slug))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service