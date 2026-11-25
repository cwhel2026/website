"""Meta Marketing API — create campaigns in PAUSED state; activate only after approval."""

from __future__ import annotations

from decimal import Decimal

import httpx

from app.config import get_settings
from app.services.marketing.budget_controls import validate_campaign_spend


async def create_paused_search_campaign(
    db,
    *,
    name: str,
    daily_budget_gbp: Decimal,
    simulation_only: bool,
) -> dict:
    gate = await validate_campaign_spend(
        db,
        platform=__import__("app.models.marketing", fromlist=["AdPlatform"]).AdPlatform.META,
        daily_budget_gbp=daily_budget_gbp,
        simulation_only=simulation_only,
    )
    if not gate.get("allowed"):
        return {"ok": False, "message": gate.get("reason")}
    if simulation_only:
        return {
            "ok": True,
            "simulation": True,
            "external_id": f"sim-meta-{name[:20]}",
            "status": "PAUSED",
            "message": "Simulated paused campaign — no Meta API call",
        }

    settings = get_settings()
    token = settings.meta_access_token
    account = settings.meta_ad_account_id
    if not token or not account:
        return {"ok": False, "message": "Meta credentials missing"}

    act = account if account.startswith("act_") else f"act_{account}"
    url = f"https://graph.facebook.com/v21.0/{act}/campaigns"
    params = {
        "name": name[:200],
        "objective": "OUTCOME_LEADS",
        "status": "PAUSED",
        "special_ad_categories": "[]",
        "is_adset_budget_sharing_enabled": "false",
        "access_token": token,
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, data=params)
            payload = resp.json()
            if resp.status_code >= 400:
                return {"ok": False, "message": payload.get("error", {}).get("message", resp.text[:200])}
    except httpx.HTTPError as exc:
        return {"ok": False, "message": str(exc)[:300]}
    return {
        "ok": True,
        "simulation": False,
        "external_id": payload.get("id"),
        "status": "PAUSED",
        "live_write_verified": True,
    }


async def pause_all_campaigns() -> dict:
    settings = get_settings()
    token = settings.meta_access_token
    account = settings.meta_ad_account_id
    if not token or not account:
        return {"ok": False, "message": "Meta not configured"}
    act = account if account.startswith("act_") else f"act_{account}"
    list_url = f"https://graph.facebook.com/v21.0/{act}/campaigns"
    params = {"fields": "id,name,status", "access_token": token, "limit": 100}
    paused = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(list_url, params=params)
        data = resp.json()
        for c in data.get("data") or []:
            if c.get("status") != "ACTIVE":
                continue
            cid = c["id"]
            pr = await client.post(
                f"https://graph.facebook.com/v21.0/{cid}",
                data={"status": "PAUSED", "access_token": token},
            )
            if pr.status_code < 400:
                paused += 1
    return {"ok": True, "paused_count": paused}