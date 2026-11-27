"""Unified integration setup centre — connection status and owner instructions."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config import get_settings
from app.services.ad_adapters import integration_state_for
from app.models.marketing import AdPlatform


def build_integration_centre() -> dict:
    s = get_settings()
    items = [
        _row(
            "companies_house",
            configured=bool(s.companies_house_api_key),
            live_read=bool(s.companies_house_api_key),
            live_write=False,
            env_vars=["COMPANIES_HOUSE_API_KEY"],
            steps="Register at developer.company-information.service.gov.uk and set API key.",
        ),
        _row(
            "google_places",
            configured=bool(s.google_places_api_key),
            live_read=bool(s.google_places_api_key),
            live_write=False,
            env_vars=["GOOGLE_PLACES_API_KEY"],
            steps="Enable Places API (New) in Google Cloud; restrict key to Places.",
        ),
        _row(
            "meta_ads",
            configured=bool(s.meta_access_token and s.meta_ad_account_id),
            live_read=bool(s.meta_access_token and s.meta_ad_account_id),
            live_write=bool(s.meta_access_token),
            env_vars=["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_PAGE_ID"],
            steps="Meta app with ads_read/ads_management. Campaigns default PAUSED until approved.",
        ),
        _row(
            "google_ads",
            configured=bool(s.google_ads_customer_id and s.google_ads_developer_token),
            live_read=bool(s.google_ads_refresh_token),
            live_write=False,
            env_vars=["GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_REFRESH_TOKEN", "GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET"],
            steps="Google Ads API OAuth + developer token in Test access first.",
        ),
        _row(
            "google_business_profile",
            configured=bool(s.gbp_account_id),
            live_read=False,
            live_write=False,
            env_vars=["GBP_ACCOUNT_ID"],
            steps="Google Business Profile API — OAuth business.manage scope.",
        ),
        _row(
            "google_analytics",
            configured=bool(s.ga4_property_id),
            live_read=False,
            live_write=False,
            env_vars=["GA4_PROPERTY_ID"],
            steps="GA4 Data API service account or OAuth.",
        ),
        _row(
            "search_console",
            configured=bool(s.gsc_site_url),
            live_read=False,
            live_write=False,
            env_vars=["GSC_SITE_URL"],
            steps="Search Console API with verified site property.",
        ),
        _row(
            "business_email",
            configured=bool(s.smtp_host and s.smtp_user and s.smtp_password),
            live_read=True,
            live_write=False,
            env_vars=["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "OUTREACH_FROM_EMAIL"],
            steps="Configure SPF/DKIM/DMARC. Enable outreach in Marketing hub budget policy.",
        ),
        _row(
            "openai",
            configured=bool(s.openai_api_key),
            live_read=bool(s.openai_api_key),
            live_write=bool(s.openai_api_key),
            env_vars=["OPENAI_API_KEY", "AI_DAILY_SPEND_LIMIT_GBP"],
            steps="Used for content studio and assistant; daily cap in settings.",
        ),
        _row(
            "telegram",
            configured=bool(s.telegram_bot_token),
            live_read=bool(s.telegram_bot_token),
            live_write=bool(s.telegram_bot_token),
            env_vars=["TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET"],
            steps="Owner bot for approvals and marketing briefs.",
        ),
        _row(
            "tiktok",
            configured=False,
            live_read=False,
            live_write=False,
            env_vars=[],
            steps="Manual publishing workflow until official Content Posting API approved.",
        ),
        _row(
            "openstreetmap",
            configured=True,
            live_read=True,
            live_write=False,
            env_vars=[],
            steps="Overpass API — no key; respect usage policy and attribute OSM.",
        ),
    ]
    items.append(
        {
            "platform": "meta_state",
            "configured": integration_state_for(AdPlatform.META).value != "not_configured",
            "state": integration_state_for(AdPlatform.META).value,
        }
    )
    pre_launch = not any(i.get("live_write_verified") for i in items)
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "integrations": items,
        "pre_launch_mode": pre_launch,
        "pre_launch_note": "Internal features work before social accounts exist. Simulated publish clearly labelled.",
    }


def _row(
    platform: str,
    *,
    configured: bool,
    live_read: bool,
    live_write: bool,
    env_vars: list[str],
    steps: str,
) -> dict:
    # This function only inspects configuration; no provider request is performed.
    live_read = False
    live_write = False
    state = "configured_untested" if configured else "not_configured"
    return {
        "platform": platform,
        "state": state,
        "credentials_present": configured,
        "live_read_verified": live_read,
        "live_write_verified": live_write,
        "railway_env_vars": env_vars,
        "setup_steps": steps,
    }