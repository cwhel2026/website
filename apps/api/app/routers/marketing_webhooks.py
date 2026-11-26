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
    from app.database import SessionLocal
    from app.services.marketing.meta_leads_service import ingest_meta_lead_payload

    settings = get_settings()
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if settings.meta_app_secret and sig.startswith("sha256="):
        expected = hmac.new(settings.meta_app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig[7:], expected):
            raise HTTPException(403, "Invalid signature")
    elif settings.meta_app_secret and not sig:
        raise HTTPException(403, "Missing signature")
    payload = json.loads(body)
    ingested: list[dict] = []
    async with SessionLocal() as db:
        for entry in payload.get("entry") or []:
            for change in entry.get("changes") or []:
                val = change.get("value") or {}
                if val.get("leadgen_id") or change.get("field") == "leadgen":
                    ingested.append(await ingest_meta_lead_payload(db, {**val, "leadgen_id": val.get("leadgen_id")}))
        await db.commit()
    return {"status": "received", "object": payload.get("object"), "ingested": ingested}


@router.get("/meta/feed")
async def meta_feed_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = "") -> Any:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == (settings.meta_webhook_verify_token or ""):
        return int(hub_challenge)
    raise HTTPException(403, "Verification failed")


@router.post("/meta/feed")
async def meta_feed_change(request: Request) -> dict:
    """Page/IG feed change — queue organic sync (no fabricated metrics)."""
    from app.database import SessionLocal
    from app.services.marketing.organic_post_sync import sync_all_organic

    settings = get_settings()
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if settings.meta_app_secret and sig.startswith("sha256="):
        expected = hmac.new(settings.meta_app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig[7:], expected):
            raise HTTPException(403, "Invalid signature")
    json.loads(body)
    async with SessionLocal() as db:
        result = await sync_all_organic(db)
        await db.commit()
    return {"status": "synced", "result": result}


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

