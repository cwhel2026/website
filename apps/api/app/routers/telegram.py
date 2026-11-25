from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.notifications import TelegramConversationMessage, TelegramProcessedUpdate
from app.services.assistant_brain import answer_question
from app.services.notifications.outbox import enqueue_notification
from app.services.telegram.client import TelegramApiError, send_message

router = APIRouter(prefix="/telegram", tags=["telegram"])
settings = get_settings()


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict[str, Any] | None = None


def _authorised_chat(chat_id: int | None, user_id: int | None) -> bool:
    if user_id is not None and user_id in settings.telegram_admin_id_list:
        return True
    owner_chat = settings.telegram_owner_chat_id
    if owner_chat is not None and chat_id == owner_chat:
        return True
    return bool(settings.telegram_admin_id_list and user_id in settings.telegram_admin_id_list)


def _reply_chat_id(update: TelegramUpdate) -> int | None:
    message = update.message or {}
    chat = message.get("chat") or {}
    return chat.get("id")


@router.post("/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    secret: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> dict[str, str]:
    if not settings.telegram_bot_token:
        raise HTTPException(503, "Telegram not configured")
    if settings.telegram_webhook_secret and secret != settings.telegram_webhook_secret:
        raise HTTPException(401, "Invalid Telegram webhook secret")
    if not update.message:
        return {"status": "ignored"}

    existing = await db.execute(
        select(TelegramProcessedUpdate).where(TelegramProcessedUpdate.update_id == update.update_id)
    )
    if existing.scalar_one_or_none():
        return {"status": "duplicate"}

    from_user = update.message.get("from") or {}
    user_id = from_user.get("id")
    chat_id = _reply_chat_id(update)
    if not _authorised_chat(chat_id, user_id):
        raise HTTPException(403, "Unauthorised Telegram user")

    text = (update.message.get("text") or "").strip()
    if not text:
        return {"status": "no_text"}

    db.add(
        TelegramProcessedUpdate(
            update_id=update.update_id,
            chat_id=chat_id,
            message_text=text[:2000],
        )
    )
    db.add(
        TelegramConversationMessage(chat_id=chat_id or 0, direction="inbound", body=text)
    )
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return {"status": "duplicate"}

    reply, _ = await answer_question(db, text)
    outbound_text = reply[:4096]
    telegram_message_id: int | None = None
    try:
        if chat_id is not None:
            result = await send_message(chat_id=chat_id, text=outbound_text)
            telegram_message_id = result.get("message_id")
    except TelegramApiError as exc:
        item = await enqueue_notification(
            db,
            channel="telegram",
            title="Telegram reply failed",
            body=f"Could not deliver assistant reply: {exc}\n\nQueued text:\n{outbound_text[:500]}",
            category="integration_failure",
            dedupe_key=f"telegram-reply-fail:{update.update_id}",
        )
        await db.commit()
        raise HTTPException(502, "Telegram delivery failed; message queued for retry") from exc

    db.add(
        TelegramConversationMessage(
            chat_id=chat_id or 0,
            direction="outbound",
            body=outbound_text,
            telegram_message_id=telegram_message_id,
        )
    )
    await db.commit()
    return {"status": "ok", "delivered": "true"}