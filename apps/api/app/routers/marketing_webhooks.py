import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.security.webhooks import (
    verify_meta_signature,
    verify_shared_secret,
    verify_subscription_challenge,
)

router = APIRouter(prefix="/marketing/webhooks", tags=["marketing-webhooks"])


def _parse_json(body: bytes) -> dict:
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise HTTPException(400, "Invalid JSON") from exc
    if not isinstance(data, dict):
        raise HTTPException(400, "Invalid payload")
    return data


@router.get("/meta/leads")
async def meta_lead_verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = "") -> Any:
    return verify_subscription_challenge(
        get_settings().meta_webhook_verify_token, hub_mode, hub_verify_token, hub_challenge
    )


@router.post("/meta/leads")
async def meta_lead_ingest(request: Request) -> dict:
    from app.database import SessionLocal
    from app.services.marketing.meta_leads_service import ingest_meta_lead_payload

    body = await request.body()
    verify_meta_signature(get_settings().meta_app_secret, body, request.headers.get("X-Hub-Signature-256"))
    payload = _parse_json(body)
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
    return verify_subscription_challenge(
        get_settings().meta_webhook_verify_token, hub_mode, hub_verify_token, hub_challenge
    )


@router.post("/meta/feed")
async def meta_feed_change(request: Request) -> dict:
    """Page/IG feed change — queue organic sync (no fabricated metrics)."""
    from app.database import SessionLocal
    from app.services.marketing.organic_post_sync import sync_all_organic

    body = await request.body()
    verify_meta_signature(get_settings().meta_app_secret, body, request.headers.get("X-Hub-Signature-256"))
    _parse_json(body)
    async with SessionLocal() as db:
        result = await sync_all_organic(db)
        await db.commit()
    return {"status": "synced", "result": result}


@router.post("/email/inbound")
async def email_inbound(request: Request) -> dict:
    """Inbound reply hook — mark replies and suppress follow-ups. Requires X-Webhook-Secret."""
    from app.database import SessionLocal
    from app.services.marketing.email.outreach_mailer import record_reply, suppress_email

    verify_shared_secret(
        get_settings().email_inbound_webhook_secret,
        request.headers.get("X-Webhook-Secret"),
        "EMAIL_INBOUND_WEBHOOK_SECRET",
    )
    data = _parse_json(await request.body())
    sender = (data.get("from") or data.get("sender") or "").strip()
    if not sender or "@" not in sender:
        return {"status": "ignored"}
    async with SessionLocal() as db:
        if "stop" in (data.get("subject") or "").lower():
            await suppress_email(db, sender, "inbound_stop")
        updated = await record_reply(db, email=sender)
        await db.commit()
    return {"status": "ok", "threads_updated": updated}
