import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.briefings import BriefingKind, BriefingRecord, DeliveryChannel, NotificationDelivery
from app.models.user import User
from app.services.briefing_service import generate_briefing

router = APIRouter(prefix="/briefings", tags=["briefings"])
settings = get_settings()


class BriefingOut(BaseModel):
    id: str
    kind: str
    content: dict
    generated_at: str


@router.post("/generate/{kind}", response_model=BriefingOut)
async def generate(
    kind: BriefingKind,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> BriefingOut:
    record = await generate_briefing(db, kind)
    delivery = NotificationDelivery(
        channel=DeliveryChannel.DASHBOARD,
        title=f"{kind.value.title()} briefing",
        body=f"Briefing {record.id}",
        briefing_id=record.id,
        status="logged",
    )
    db.add(delivery)
    if settings.telegram_bot_token and settings.telegram_admin_id_list:
        db.add(
            NotificationDelivery(
                channel=DeliveryChannel.TELEGRAM,
                title=f"{kind.value.title()} briefing",
                body="Telegram delivery not yet implemented — queued as stub",
                briefing_id=record.id,
                status="stub_not_sent",
            )
        )
    await db.commit()
    content = json.loads(record.content_json)
    return BriefingOut(
        id=str(record.id),
        kind=record.kind.value,
        content=content,
        generated_at=record.generated_at.isoformat(),
    )


@router.get("/latest/{kind}", response_model=BriefingOut)
async def latest(
    kind: BriefingKind,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> BriefingOut:
    result = await db.execute(
        select(BriefingRecord)
        .where(BriefingRecord.kind == kind)
        .order_by(BriefingRecord.generated_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(404, "No briefing generated yet")
    return BriefingOut(
        id=str(record.id),
        kind=record.kind.value,
        content=json.loads(record.content_json),
        generated_at=record.generated_at.isoformat(),
    )