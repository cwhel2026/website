import hashlib
import hmac
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from app.config import get_settings

router = APIRouter(prefix="/marketing/webhooks", tags=["marketing-webhooks"])


@router.get("/meta/leads")
async def meta_lead_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = "") -> Any:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == (settings.meta_webhook_verify_token or ""):
        return int(hub_challenge)
    raise HTTPException(403, "Verification failed")


@router.post("/meta/leads")
async def meta_lead_ingest(request: Request) -> dict:
    settings = get_settings()
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if settings.meta_app_secret and sig.startswith("sha256="):
        expected = hmac.new(settings.meta_app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig[7:], expected):
            raise HTTPException(403, "Invalid signature")
    payload = json.loads(body)
    return {"status": "received", "object": payload.get("object"), "entries": len(payload.get("entry") or [])}


@router.post("/email/inbound")
async def email_inbound(request: Request) -> dict:
    """Minimal inbound hook — mark replies and suppress follow-ups."""
    from app.database import SessionLocal
    from app.services.marketing.email.outreach_mailer import record_reply, suppress_email

    data = await request.json()
    sender = (data.get("from") or data.get("sender") or "").strip()
    if not sender or "@" not in sender:
        return {"status": "ignored"}
    async with SessionLocal() as db:
        await suppress_email(db, sender, "inbound_stop") if "stop" in (data.get("subject") or "").lower() else None
        updated = await record_reply(db, email=sender)
        await db.commit()
    return {"status": "ok", "threads_updated": updated}

