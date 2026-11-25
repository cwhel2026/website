import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.notifications import TelegramConversationMessage, TelegramProcessedUpdate
from app.models.user import User
from app.services.assistant_brain import answer_question
from app.services.notifications.outbox import enqueue_notification
from app.services.telegram.client import TelegramApiError, send_message
from app.services.telegram.register import (
    WebhookRegistrationError,
    normalise_telegram_webhook_secret,
    register_telegram_webhook,
)
from app.services.telegram.webhook_info import fetch_webhook_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

START_MESSAGE = (
    "Revive My Drive assistant is connected.\n\n"
    "Ask about today's jobs, weather, quotations, or marketing — private owner access only."
)


class TelegramUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    update_id: int
    message: dict[str, Any] | None = None


def _extract_message(update: TelegramUpdate) -> dict[str, Any] | None:
    if update.message:
        return update.message
    return None


def _authorised_chat(chat_id: int | None, user_id: int | None) -> bool:
    cfg = get_settings()
    admins = cfg.telegram_admin_id_list
    if not admins:
        return False
    if user_id is not None and user_id in admins:
        return True
    owner_chat = cfg.telegram_owner_chat_id
    if owner_chat is not None and chat_id == owner_chat:
        return True
    return False


def _reply_chat_id(message: dict[str, Any] | None) -> int | None:
    if not message:
        return None
    chat = message.get("chat") or {}
    return chat.get("id")


async def _safe_send(chat_id: int, text: str) -> int | None:
    try:
        result = await send_message(chat_id=chat_id, text=text[:4096])
        return result.get("message_id")
    except TelegramApiError as exc:
        logger.warning("Telegram outbound failed for chat %s: %s", chat_id, exc)
        return None


@router.post("/register-webhook")
async def telegram_register_webhook(
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    """Register or refresh the Telegram webhook from server env (no secrets returned)."""
    try:
        return register_telegram_webhook()
    except WebhookRegistrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/register-webhook/bootstrap")
async def telegram_register_webhook_bootstrap(
    setup_key: Annotated[str | None, Header(alias="X-Telegram-Setup-Key")] = None,
) -> dict[str, Any]:
    """
    One-off bootstrap when shell access is unavailable.
    Set TELEGRAM_WEBHOOK_SETUP_KEY on the API service, call once, then remove the key.
    """
    cfg = get_settings()
    expected = (cfg.telegram_webhook_setup_key or "").strip()
    if not expected or setup_key != expected:
        raise HTTPException(status_code=401, detail="Invalid setup key")
    try:
        return register_telegram_webhook()
    except WebhookRegistrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status")
async def telegram_integration_status(
    _: Annotated[User, Depends(get_current_admin)],
) -> dict[str, Any]:
    """Owner dashboard diagnostic — no tokens exposed."""
    expected_path_suffix = "/api/v1/telegram/webhook"
    info = await fetch_webhook_info()
    cfg = get_settings()
    base = (cfg.public_api_base_url or "").rstrip("/")
    expected_url = f"{base}{expected_path_suffix}" if base else None
    url_ok = bool(
        expected_url
        and info.get("webhook_url")
        and str(info["webhook_url"]).rstrip("/") == expected_url.rstrip("/")
    )
    return {
        "bot_token_set": bool(cfg.telegram_bot_token),
        "webhook_secret_set": bool(cfg.telegram_webhook_secret),
        "admin_ids_configured": len(cfg.telegram_admin_id_list),
        "public_api_base_url": base or None,
        "expected_webhook_url": expected_url,
        "telegram_webhook": info,
        "webhook_url_matches_expected": url_ok if expected_url else None,
    }


@router.post("/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    secret: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> JSONResponse:
    """Always return HTTP 200 to Telegram when the secret is valid (except 401/503)."""
    cfg = get_settings()
    if not cfg.telegram_bot_token:
        raise HTTPException(503, "Telegram not configured")
    expected = normalise_telegram_webhook_secret(cfg.telegram_webhook_secret or "")
    if expected and secret != expected:
        raise HTTPException(401, "Invalid Telegram webhook secret")

    message = _extract_message(update)
    if not message:
        return JSONResponse({"status": "ignored", "reason": "no_message"})

    existing = await db.execute(
        select(TelegramProcessedUpdate).where(TelegramProcessedUpdate.update_id == update.update_id)
    )
    if existing.scalar_one_or_none():
        return JSONResponse({"status": "duplicate"})

    from_user = message.get("from") or {}
    user_id = from_user.get("id")
    chat_id = _reply_chat_id(message)
    text = (message.get("text") or "").strip()

    if chat_id is None:
        return JSONResponse({"status": "ignored", "reason": "no_chat_id"})

    if not _authorised_chat(chat_id, user_id):
        hint = (
            "This bot is private (Revive My Drive owner assistant).\n\n"
            f"Your Telegram user ID is: {user_id}\n\n"
            "Ask the account owner to add this number to TELEGRAM_ADMIN_IDS on the API service, "
            "then try again."
        )
        if not cfg.telegram_admin_id_list:
            hint = (
                "Telegram is not fully configured: TELEGRAM_ADMIN_IDS is empty on the server.\n\n"
                f"Your Telegram user ID is: {user_id}\n\n"
                "Add it to Railway API variables and redeploy."
            )
        await _safe_send(chat_id, hint)
        return JSONResponse({"status": "unauthorised", "delivered_hint": True})

    if not text:
        await _safe_send(chat_id, "Send a text message or use /start")
        return JSONResponse({"status": "no_text", "delivered_hint": True})

    db.add(
        TelegramProcessedUpdate(
            update_id=update.update_id,
            chat_id=chat_id,
            message_text=text[:2000],
        )
    )
    db.add(
        TelegramConversationMessage(chat_id=chat_id, direction="inbound", body=text)
    )
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return JSONResponse({"status": "duplicate"})

    if text == "/start" or text.startswith("/start "):
        outbound_text = START_MESSAGE
        reply_meta = {}
    else:
        try:
            reply, reply_meta = await answer_question(db, text)
            outbound_text = reply[:4096]
        except Exception as exc:
            logger.exception("Assistant failed for Telegram message")
            outbound_text = (
                "I could not process that request right now. "
                "Check API logs and OPENAI_API_KEY on Railway."
            )
            reply_meta = {"error": str(exc)[:200]}

    telegram_message_id = await _safe_send(chat_id, outbound_text)
    if telegram_message_id is None:
        await enqueue_notification(
            db,
            channel="telegram",
            title="Telegram reply failed",
            body=outbound_text[:500],
            category="integration_failure",
            dedupe_key=f"telegram-reply-fail:{update.update_id}",
        )
        await db.commit()
        return JSONResponse({"status": "send_failed", "queued": True})

    db.add(
        TelegramConversationMessage(
            chat_id=chat_id,
            direction="outbound",
            body=outbound_text,
            telegram_message_id=telegram_message_id,
        )
    )
    await db.commit()
    return JSONResponse(
        {"status": "ok", "delivered": True, "meta_keys": list(reply_meta.keys()) if reply_meta else []}
    )