import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.marketing_ops import ContentPlatform, MarketingContentItem, MarketingMediaAsset
from app.models.user import User
from app.services.marketing.before_after import build_before_after_package, ingest_marketing_photo
from app.services.marketing.content_studio import generate_platform_content

router = APIRouter(prefix="/marketing/content", tags=["marketing-content"])


class GenerateIn(BaseModel):
    platform: ContentPlatform
    brief: str = Field(min_length=4)
    territory_name: str | None = None


@router.post("/generate")
async def generate_content(
    body: GenerateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    item = await generate_platform_content(
        db, platform=body.platform, brief=body.brief, territory_name=body.territory_name
    )
    await db.commit()
    return {"id": str(item.id), "status": item.status.value, "body_preview": item.body_text[:500]}


@router.get("/items")
async def list_content(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = (
        await db.execute(select(MarketingContentItem).order_by(MarketingContentItem.created_at.desc()).limit(50))
    ).scalars().all()
    return [
        {"id": str(r.id), "platform": r.platform.value, "title": r.title, "status": r.status.value}
        for r in rows
    ]


@router.post("/media/upload")
async def upload_media(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    file: UploadFile = File(...),
    job_id: str | None = Form(None),
    category: str = Form("general"),
) -> dict:
    data = await file.read()
    if len(data) > 12_000_000:
        raise HTTPException(400, "File too large")
    jid = uuid.UUID(job_id) if job_id else None
    asset = await ingest_marketing_photo(
        db,
        data=data,
        filename=file.filename or "upload.jpg",
        job_id=jid,
        telegram_file_id=None,
        is_before=category == "before",
        customer_permission=False,
    )
    await db.commit()
    return {"asset_id": str(asset.id), "storage_key": asset.storage_key}


class BeforeAfterIn(BaseModel):
    job_id: uuid.UUID
    before_asset_id: uuid.UUID
    after_asset_id: uuid.UUID
    customer_permission: bool


@router.post("/before-after")
async def before_after(
    body: BeforeAfterIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await build_before_after_package(
        db,
        job_id=body.job_id,
        before_asset_id=body.before_asset_id,
        after_asset_id=body.after_asset_id,
        customer_permission=body.customer_permission,
    )
    await db.commit()
    if not result.get("ok"):
        raise HTTPException(400, result.get("message", "Failed"))
    return result