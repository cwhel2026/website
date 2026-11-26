"""Meta Conversions API — server events when configured; GDPR consent required upstream."""

from __future__ import annotations

import hashlib
import time

import httpx

from app.config import get_settings

GRAPH = "https://graph.facebook.com/v21.0"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


async def send_capi_event(
    *,
    event_name: str,
    event_id: str,
    email: str | None = None,
    phone: str | None = None,
    custom_data: dict | None = None,
    consent_attested: bool = False,
) -> dict:
    settings = get_settings()
    pixel = settings.meta_pixel_id
    token = settings.meta_capi_dataset_token or settings.meta_access_token
    if not pixel or not token:
        return {"ok": False, "message": "META_PIXEL_ID and token required for CAPI"}
    if not consent_attested:
        return {"ok": False, "message": "consent_attested required before sending CAPI events"}
    user_data: dict = {}
    if email:
        user_data["em"] = [_sha256(email)]
    if phone:
        user_data["ph"] = [_sha256(phone)]
    body = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(time.time()),
                "event_id": event_id,
                "action_source": "website",
                "user_data": user_data,
                "custom_data": custom_data or {},
            }
        ],
    }
    url = f"{GRAPH}/{pixel}/events"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, params={"access_token": token}, json=body)
            data = resp.json()
            if resp.status_code >= 400:
                return {"ok": False, "message": data.get("error", {}).get("message", resp.text[:200])}
            return {"ok": True, "events_received": data.get("events_received"), "fbtrace_id": data.get("fbtrace_id")}
    except httpx.HTTPError as exc:
        return {"ok": False, "message": str(exc)[:300]}