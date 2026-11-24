from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services.assistant_brain import answer_question

router = APIRouter(prefix="/telegram", tags=["telegram"])
settings = get_settings()


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict[str, Any] | None = None


@router.post("/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    if not settings.telegram_bot_token:
        raise HTTPException(503, "Telegram not configured")
    if not update.message:
        return {"status": "ignored"}
    from_user = update.message.get("from") or {}
    user_id = from_user.get("id")
    if user_id not in settings.telegram_admin_id_list:
        raise HTTPException(403, "Unauthorised Telegram user")
    text = update.message.get("text") or ""
    if not text:
        return {"status": "no_text"}
    reply, _ = await answer_question(db, text)
    return {"status": "ok", "reply": reply}