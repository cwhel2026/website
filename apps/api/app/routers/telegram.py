import hmac
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
    "🟡 SurfaceCoat | COMMAND CENTRE\n"
    "Private owner assistant\n\n"
    "📅 /today — today’s jobs\n"
    "🗓 /diary — upcoming appointments\n"
    "📋 /quotes — quotation overview\n"
    "💷 /finance — business finances\n"
    "🌦 /weather — weather intelligence\n"
    "🔐 /approvals — review pending decisions\n"
    "📆 /schedule — coating deadlines\n\n"
    "Ask a business question or send a receipt photo (OCR must be configured)."

)


def format_business_report(heading: str, data: dict) -> str:
    lines = [f"🟡 SurfaceCoat | {heading}", ""]
    for key, value in data.items():
        label = key.replace("_", " ").capitalize()
        if isinstance(value, list):
            lines.append(f"{label}:")
            if not value:
                lines.append("  None recorded")
            for item in value:
                if isinstance(item, dict):
                    lines.append("• " + " | ".join(f"{k.replace('_', ' ')}: {v if v is not None else 'unknown'}" for k, v in item.items()))
                else:
                    lines.append(f"• {item}")
        elif isinstance(value, dict):
            lines.extend(f"• {k}: {v}" for k, v in value.items())
        else:
            lines.append(f"{label}: {value}")
    lines.extend(["", "Read-only report. Review changes in the dashboard."])
    return "\n".join(lines)


class TelegramUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    update_id: int
    message: dict[str, Any] | None = None


def _largest_photo_file_id(message: dict[str, Any]) -> str | None:
    photos = message.get("photo") or []
    if not photos:
        return None
    best = max(photos, key=lambda p: p.get("file_size") or 0)
    return best.get("file_id")


def _extract_message(update: TelegramUpdate) -> dict[str, Any] | None:
    if update.message:
        return update.message
    return None


def _authorised_chat(chat_id: int | None, user_id: int | None) -> bool:
    cfg = get_settings()
    admins = cfg.telegram_admin_id_list
    if not admins:
        return False
    return user_id is not None and user_id in admins and chat_id == user_id


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
    if not expected or not setup_key or not hmac.compare_digest(setup_key, expected):
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
    if not expected:
        raise HTTPException(503, "Telegram webhook secret not configured")
    if not secret or not hmac.compare_digest(secret, expected):
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
    text = (message.get("text") or "").strip()[:4000]

    if chat_id is None:
        return JSONResponse({"status": "ignored", "reason": "no_chat_id"})

    if not _authorised_chat(chat_id, user_id):
        hint = (
            "This bot is private (SurfaceCoat owner assistant).\n\n"
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

    photo_id = _largest_photo_file_id(message)
    caption = (message.get("caption") or "").strip()
    if photo_id and caption.lower().startswith("#marketing"):
        from app.services.finance.bookkeeping.receipt_processor import download_telegram_file
        from app.services.marketing.before_after import ingest_marketing_photo

        db.add(
            TelegramProcessedUpdate(
                update_id=update.update_id,
                chat_id=chat_id,
                message_text="[marketing_photo]",
            )
        )
        try:
            await db.flush()
            data, fname = await download_telegram_file(photo_id)
            is_before = "before" in caption.lower()
            asset = await ingest_marketing_photo(
                db,
                data=data,
                filename=fname or "telegram.jpg",
                job_id=None,
                telegram_file_id=photo_id,
                is_before=is_before,
                customer_permission="#permission_granted" in caption.lower().split(),
            )
            from app.services.marketing.job_media_telegram import parse_job_reference, stage_telegram_photo

            phase = "before" if is_before else "after"
            staged = await stage_telegram_photo(db, asset=asset, caption=caption, phase=phase)
            await db.commit()
            ref = staged.get("job_reference") or parse_job_reference(caption)
            msg = f"Marketing photo stored ({asset.category})."
            if ref:
                msg += f" Job ref: {ref} ({'matched' if staged.get('job_found') else 'not found'})."
            if staged.get("before_after_package", {}).get("ok"):
                msg += " Before/after package queued for approval."
            elif phase == "after" and not ("#permission_granted" in caption.lower().split()):
                msg += " Add '#permission_granted' in caption when customer has agreed to marketing use."
            await _safe_send(chat_id, msg)
            return JSONResponse({"status": "marketing_media_ok", "asset_id": str(asset.id)})
        except IntegrityError:
            await db.rollback()
            return JSONResponse({"status": "duplicate"})
        except Exception as exc:
            await db.rollback()
            await _safe_send(chat_id, "Could not store marketing photo. Check integration health.")
            return JSONResponse({"status": "marketing_media_failed"})

    if photo_id and not text:
        from app.services.finance.bookkeeping.receipt_processor import (
            ingest_telegram_receipt,
            summarise_receipt_reply,
        )

        db.add(
            TelegramProcessedUpdate(
                update_id=update.update_id,
                chat_id=chat_id,
                message_text="[receipt_photo]",
            )
        )
        try:
            await db.flush()
            receipt, detail = await ingest_telegram_receipt(db, photo_id)
            outbound_text = summarise_receipt_reply(receipt, detail)
            await db.commit()
            await _safe_send(chat_id, outbound_text)
            return JSONResponse({"status": "receipt_ok", "receipt_id": str(receipt.id)})
        except IntegrityError:
            await db.rollback()
            return JSONResponse({"status": "duplicate"})
        except Exception as exc:
            logger.exception("Receipt ingest failed")
            await db.rollback()
            await _safe_send(
                chat_id,
                "Could not process that receipt — try a clearer photo or check API logs.",
            )
            return JSONResponse({"status": "receipt_failed"})

    if not text:
        await _safe_send(chat_id, "Send text, a receipt photo, or /start")
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

    if text in {"/start", "/help"} or text.startswith("/start "):
        outbound_text = START_MESSAGE
        reply_meta = {}
    else:
        try:
            from app.services.finance.telegram_finance import answer_finance_question

            from app.services.assistant_tools import (
                tool_jobs_today, tool_jobs_next_week, tool_quotations_awaiting,
                tool_pending_approvals, tool_rain_risk_appointments,
                tool_analytics_snapshot, tool_schedule_proposals,
            )
            commands = {
                "/today": ("TODAY'S CONFIRMED JOBS", tool_jobs_today),
                "/diary": ("NEXT SEVEN DAYS", tool_jobs_next_week),
                "/quotes": ("QUOTATIONS AWAITING APPROVAL", tool_quotations_awaiting),
                "/finance": ("30-DAY BUSINESS FINANCES", tool_analytics_snapshot),
                "/weather": ("KNOWN COATING WEATHER RISKS", tool_rain_risk_appointments),
                "/approvals": ("PENDING APPROVALS", tool_pending_approvals),
                "/schedule": ("COATING PROPOSALS FOR REVIEW", tool_schedule_proposals),
            }
            command = commands.get(text.lower())
            if command:
                heading, handler = command
                data = await handler(db)
                reply = format_business_report(heading, data)
                reply_meta = {"database_report": True}
            else:
                finance_reply = await answer_finance_question(db, text)
                if finance_reply:
                    reply, reply_meta = finance_reply, {}
                else:
                    reply, reply_meta = await answer_question(db, text)
            outbound_text = reply[:4096]
        except Exception as exc:
            logger.exception("Assistant failed for Telegram message")
            outbound_text = (
                "I could not process that request right now. "
                "Check API logs and OPENAI_API_KEY on Railway."
            )
            reply_meta = {"error": "assistant_unavailable"}

    telegram_message_id = await _safe_send(chat_id, outbound_text)
    if telegram_message_id is None:
        await enqueue_notification(
            db,
            channel="telegram",
            title="",
            body=outbound_text[:4096],
            category="assistant_reply",
            payload={"reply_chat_id": chat_id},
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