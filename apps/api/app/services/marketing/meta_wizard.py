"""Honest Meta connection checklist — permissions and app review requirements."""

from __future__ import annotations

from app.config import get_settings
from app.services.marketing.meta_graph_client import account_spend_last_7d, fetch_page_posts


def meta_connection_wizard() -> dict:
    s = get_settings()
    steps = [
        {
            "id": "business",
            "title": "Meta Business Portfolio",
            "done_hint": "Business verified in Meta Business Settings",
            "url": "https://business.facebook.com/settings",
        },
        {
            "id": "app",
            "title": "Developer app",
            "done_hint": "App created at developers.facebook.com with Marketing API product",
            "url": "https://developers.facebook.com/apps/",
        },
        {
            "id": "token",
            "title": "System user or long-lived token",
            "env": ["META_ACCESS_TOKEN"],
            "permissions": [
                "pages_show_list",
                "pages_read_engagement",
                "pages_read_user_content",
                "instagram_basic",
                "instagram_manage_insights",
                "ads_read",
                "ads_management",
                "leads_retrieval",
                "business_management",
            ],
            "app_review_note": "ads_management and leads_retrieval typically require App Review.",
        },
        {
            "id": "page",
            "title": "Facebook Page",
            "env": ["META_PAGE_ID"],
        },
        {
            "id": "instagram",
            "title": "Instagram professional account",
            "env": ["META_INSTAGRAM_ACTOR_ID"],
            "note": "IG account must be linked to the Page (Instagram Graph user id).",
        },
        {
            "id": "ad_account",
            "title": "Ad account",
            "env": ["META_AD_ACCOUNT_ID"],
            "format": "act_123456789",
        },
        {
            "id": "webhooks",
            "title": "Webhooks",
            "env": ["META_APP_SECRET", "META_WEBHOOK_VERIFY_TOKEN", "PUBLIC_API_BASE_URL"],
            "callbacks": [
                "/api/v1/marketing/webhooks/meta/leads",
                "/api/v1/marketing/webhooks/meta/feed",
            ],
            "fields": ["leadgen", "feed"],
        },
        {
            "id": "pixel_capi",
            "title": "Pixel & Conversions API",
            "env": ["META_PIXEL_ID", "META_CAPI_DATASET_TOKEN"],
            "optional_until": "You drive paid traffic to the website",
            "consent": "UK GDPR / PECR — use site consent before sending events",
        },
    ]
    configured = {
        "META_ACCESS_TOKEN": bool(s.meta_access_token),
        "META_PAGE_ID": bool(s.meta_page_id),
        "META_INSTAGRAM_ACTOR_ID": bool(s.meta_instagram_actor_id),
        "META_AD_ACCOUNT_ID": bool(s.meta_ad_account_id),
        "META_APP_SECRET": bool(s.meta_app_secret),
        "META_WEBHOOK_VERIFY_TOKEN": bool(s.meta_webhook_verify_token),
        "META_PIXEL_ID": bool(getattr(s, "meta_pixel_id", None)),
    }
    return {
        "brand": "SurfaceCoat Ltd",
        "api_version": "v21.0",
        "steps": steps,
        "configured": configured,
        "docs": "SURFACECOAT_META_UPGRADE.md",
        "no_live_spend_until": "Marketing → Budget → live spend approval",
    }


async def run_connection_tests() -> dict:
    wizard = meta_connection_wizard()
    page = await fetch_page_posts(limit=3)
    spend = await account_spend_last_7d()
    return {
        "wizard": wizard,
        "tests": {
            "page_posts": {
                "ok": page.get("ok"),
                "message": page.get("message"),
                "sample_count": len(page.get("posts") or []),
            },
            "ad_insights": spend,
        },
        "fabricated": False,
    }