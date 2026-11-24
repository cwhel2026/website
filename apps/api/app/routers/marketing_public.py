from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.marketing import FlyerCampaign

router = APIRouter(prefix="/marketing", tags=["marketing-public"])


@router.get("/flyer/{qr_slug}")
async def flyer_landing_meta(qr_slug: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(FlyerCampaign).where(FlyerCampaign.qr_slug == qr_slug))
    flyer = result.scalar_one_or_none()
    if flyer is None:
        raise HTTPException(404, "Unknown campaign")
    return {
        "name": flyer.name,
        "landing_path": flyer.landing_path,
        "attribution_source": f"flyer_{qr_slug}",
    }