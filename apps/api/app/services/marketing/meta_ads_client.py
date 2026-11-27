"""Meta Marketing API — read-only insights when credentials are configured."""

from __future__ import annotations

import httpx

from app.config import get_settings


async def fetch_account_insights(*, days: int = 7) -> dict:
    settings = get_settings()
    token = settings.meta_access_token
    account_id = settings.meta_ad_account_id
    if not token or not account_id:
        return {
            "ok": False,
            "live_read_verified": False,
            "message": "META_ACCESS_TOKEN and META_AD_ACCOUNT_ID required.",
        }
    act = account_id if account_id.startswith("act_") else f"act_{account_id}"
    url = f"https://graph.facebook.com/v21.0/{act}/insights"
    params = {
        "fields": "spend,impressions,clicks,actions",
        "date_preset": "last_7d" if days == 7 else "last_30d",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return {"ok": False, "live_read_verified": False, "message": "Meta insights request failed"}
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        return {"ok": False, "live_read_verified": False, "message": "Invalid Meta response"}
    rows = data["data"]
    spend = sum(float(r.get("spend", 0)) for r in rows)
    return {
        "ok": True,
        "live_read_verified": True,
        "spend_gbp": spend,
        "rows": rows,
        "source": "https://developers.facebook.com/docs/marketing-api/insights",
    }