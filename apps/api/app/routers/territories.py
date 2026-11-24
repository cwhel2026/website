from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models.territory import PostcodeDistrict, Territory
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.territory import (
    PostcodeDistrictCreate,
    TerritoryCreate,
    TerritoryOut,
    TerritoryUpdate,
)

router = APIRouter(prefix="/territories", tags=["territories"])


@router.get("", response_model=list[TerritoryOut])
async def list_territories(db: Annotated[AsyncSession, Depends(get_db)]) -> list[Territory]:
    result = await db.execute(
        select(Territory)
        .options(
            selectinload(Territory.localities),
            selectinload(Territory.postcode_districts),
        )
        .order_by(Territory.code)
    )
    return list(result.scalars().all())


@router.get("/{territory_id}", response_model=TerritoryOut)
async def get_territory(
    territory_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> Territory:
    result = await db.execute(
        select(Territory)
        .options(
            selectinload(Territory.localities),
            selectinload(Territory.postcode_districts),
        )
        .where(Territory.id == territory_id)
    )
    territory = result.scalar_one_or_none()
    if territory is None:
        raise HTTPException(status_code=404, detail="Territory not found")
    return territory


@router.patch("/{territory_id}", response_model=TerritoryOut)
async def update_territory(
    territory_id: UUID,
    body: TerritoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> Territory:
    result = await db.execute(select(Territory).where(Territory.id == territory_id))
    territory = result.scalar_one_or_none()
    if territory is None:
        raise HTTPException(status_code=404, detail="Territory not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(territory, field, value)
    await db.commit()
    await db.refresh(territory)
    return territory


@router.post("", response_model=TerritoryOut)
async def create_territory(
    body: TerritoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> Territory:
    existing = await db.execute(select(Territory).where(Territory.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Territory code already exists")
    territory = Territory(**body.model_dump())
    db.add(territory)
    await db.commit()
    await db.refresh(territory)
    return territory


@router.post("/postcode-districts", response_model=MessageResponse)
async def add_postcode_district(
    body: PostcodeDistrictCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> MessageResponse:
    result = await db.execute(select(Territory).where(Territory.code == body.territory_code))
    territory = result.scalar_one_or_none()
    if territory is None:
        raise HTTPException(status_code=404, detail="Territory not found")
    district = body.district.strip().upper()
    db.add(PostcodeDistrict(district=district, territory_id=territory.id))
    await db.commit()
    return MessageResponse(message=f"Postcode district {district} added")