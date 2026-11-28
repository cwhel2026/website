"""Meta Graph API v21.0 — read posts, insights, account spend (no fabricated data)."""

from __future__ import annotations

import httpx

from app.config import get_settings

GRAPH = "https://graph.facebook.com/v21.0"


async def graph_get(path: str, params: dict | None = None) -> dict:
    settings = get_settings()
    token = settings.meta_access_token
    if not token:
        return {"ok": False, "message": "META_ACCESS_TOKEN not configured"}
    q = {k: v for k, v in (params or {}).items() if k != "access_token"}
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.get(f"{GRAPH}/{path.lstrip('/')}", params=q, headers={"Authorization": f"Bearer {token}"})
            data = resp.json()
            if not isinstance(data, dict):
                return {"ok": False, "message": "Invalid Meta response"}
            if resp.status_code >= 400:
                err = data.get("error", {})
                return {"ok": False, "message": err.get("message", resp.text[:200]), "code": err.get("code")}
            return {"ok": True, "data": data}
    except (httpx.HTTPError, ValueError, TypeError):
        return {"ok": False, "message": "Meta read request failed"}


async def fetch_page_posts(limit: int = 25) -> dict:
    settings = get_settings()
    page_id = settings.meta_page_id
    if not page_id:
        return {"ok": False, "message": "META_PAGE_ID required", "posts": []}
    fields = "id,message,created_time,permalink_url,full_picture,attachments,shares"
    res = await graph_get(
        f"{page_id}/published_posts",
        {"fields": fields, "limit": str(limit)},
    )
    if not res.get("ok"):
        return {**res, "posts": []}
    posts = (res["data"] or {}).get("data") or []
    return {"ok": True, "posts": posts, "live_read_verified": True}


async def fetch_instagram_media(limit: int = 25) -> dict:
    settings = get_settings()
    ig_id = settings.meta_instagram_actor_id
    if not ig_id:
        return {"ok": False, "message": "META_INSTAGRAM_ACTOR_ID required", "posts": []}
    fields = "id,caption,timestamp,media_type,media_url,permalink,like_count,comments_count"
    res = await graph_get(f"{ig_id}/media", {"fields": fields, "limit": str(limit)})
    if not res.get("ok"):
        return {**res, "posts": []}
    posts = (res["data"] or {}).get("data") or []
    return {"ok": True, "posts": posts, "live_read_verified": True}


async def fetch_post_insights(platform: str, external_id: str) -> dict:
    if platform == "facebook":
        fields = "post_impressions,post_engaged_users,post_clicks"
        res = await graph_get(f"{external_id}/insights", {"metric": ",".join(fields.split(","))})
    else:
        fields = "reach,impressions,engagement,saved"
        res = await graph_get(f"{external_id}/insights", {"metric": fields})
    if not res.get("ok"):
        return {"ok": False, "metrics": {}, "message": res.get("message")}
    rows = (res["data"] or {}).get("data") or []
    metrics = {r.get("name"): r.get("values") for r in rows}
    return {"ok": True, "metrics": metrics, "source": "meta_insights"}


async def account_spend_last_7d() -> dict:
    from app.services.marketing.meta_ads_client import fetch_account_insights

    return await fetch_account_insights(days=7)