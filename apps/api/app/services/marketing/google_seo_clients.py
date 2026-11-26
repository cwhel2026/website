"""Google GBP, Search Console, GA4 — connection verification (credentials via env)."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.config import get_settings

class GoogleClientResult:
    def __init__(self, *, ok: bool, provider: str, live: bool, message: str, data: dict | None = None):
        self.ok = ok
        self.provider = provider
        self.live = live
        self.message = message
        self.data = data or {}


async def verify_ga4() -> GoogleClientResult:
    s = get_settings()
    if not s.ga4_property_id:
        return GoogleClientResult(ok=False, provider="ga4", live=False, message="GA4_PROPERTY_ID not set")
    if not s.google_ads_refresh_token:
        return GoogleClientResult(
            ok=True,
            provider="ga4",
            live=False,
            message="Awaiting OAuth refresh token — mock metrics unavailable",
            data={"status": "awaiting_credentials"},
        )
    return GoogleClientResult(
        ok=True,
        provider="ga4",
        live=False,
        message="Implement Data API runReport when refresh token stored",
        data={"property_id": s.ga4_property_id},
    )


async def verify_search_console() -> GoogleClientResult:
    s = get_settings()
    if not s.gsc_site_url:
        return GoogleClientResult(ok=False, provider="gsc", live=False, message="GSC_SITE_URL not set")
    return GoogleClientResult(
        ok=True,
        provider="gsc",
        live=False,
        message="Awaiting OAuth — use Search Console API searchanalytics.query when connected",
        data={"site_url": s.gsc_site_url},
    )


async def verify_gbp() -> GoogleClientResult:
    s = get_settings()
    if not s.gbp_account_id:
        return GoogleClientResult(ok=False, provider="gbp", live=False, message="GBP_ACCOUNT_ID not set")
    return GoogleClientResult(
        ok=True,
        provider="gbp",
        live=False,
        message="Awaiting business.manage OAuth scope",
        data={"account_id": s.gbp_account_id},
    )


async def seo_dashboard_snapshot() -> dict:
    ga4 = await verify_ga4()
    gsc = await verify_search_console()
    gbp = await verify_gbp()
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "ga4": ga4.__dict__,
        "gsc": gsc.__dict__,
        "gbp": gbp.__dict__,
        "impressions": None,
        "clicks": None,
        "note": "Unknown metrics omitted — not zero",
    }