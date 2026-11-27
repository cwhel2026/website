"""Pre-launch checklist — honest statuses for unconfigured owner accounts."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config import get_settings
from app.services.marketing.integration_setup import build_integration_centre


CHECKLIST_ITEMS = [
    ("business_registered", "Business registered with Companies House", False),
    ("domain_dns", "Domain and SSL live", False),
    ("privacy_policy", "Privacy policy published on website", True),
    ("meta_business", "Meta Business Portfolio + Page + Instagram", False),
    ("meta_ads_account", "Meta ad account created", False),
    ("google_ads_account", "Google Ads account", False),
    ("google_business_profile", "Google Business Profile", False),
    ("business_email", "Business email / SMTP", False),
    ("marketing_volume", "Marketing media volume mounted", False),
    ("live_spend_policy", "Owner reviewed budget policy (keep blocked until launch)", True),
]


def assess_launch_readiness() -> dict:
    s = get_settings()
    centre = build_integration_centre()
    by_platform = {i["platform"]: i for i in centre["integrations"] if "platform" in i}

    def status_for(key: str) -> str:
        mapping = {
            "meta_business": by_platform.get("meta_ads", {}),
            "meta_ads_account": by_platform.get("meta_ads", {}),
            "google_ads_account": by_platform.get("google_ads", {}),
            "google_business_profile": by_platform.get("google_business_profile", {}),
            "business_email": by_platform.get("business_email", {}),
        }
        row = mapping.get(key)
        if row and row.get("live_write_verified"):
            return "write_access_verified"
        if row and row.get("live_read_verified"):
            return "read_access_verified"
        if row and row.get("credentials_present"):
            return "configured_untested"
        if key == "marketing_volume":
            return "configured_untested" if s.marketing_media_dir.startswith("/data") else "not_configured"
        if key == "domain_dns":
            return "configured_untested" if s.public_api_base_url else "not_configured"
        return "not_configured" if key not in ("privacy_policy", "live_spend_policy") else "configured_untested"

    items = []
    blockers: list[str] = []
    for key, label, optional in CHECKLIST_ITEMS:
        st = status_for(key)
        if st not in ("read_access_verified", "write_access_verified") and not optional:
            blockers.append(label)
        items.append({"key": key, "label": label, "status": st, "optional": optional})

    ready_score = sum(1 for i in items if i["status"] in ("read_access_verified", "write_access_verified")) 
    return {
        "assessed_at": datetime.now(UTC).isoformat(),
        "pre_launch": True,
        "items": items,
        "external_blockers": blockers,
        "ready_score": ready_score,
        "ready_total": len(items),
        "can_use_offline_features": True,
        "message": "Internal marketing (research drafts, content, prospects) works before social accounts exist.",
        "integrations": centre["integrations"],
    }