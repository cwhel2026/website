"""Google Ads API — connection verification only until OAuth customer setup is complete."""

from app.config import get_settings


def google_ads_connection_status() -> dict:
    settings = get_settings()
    customer_id = settings.google_ads_customer_id
    dev_token = settings.google_ads_developer_token
    if not customer_id or not dev_token:
        return {
            "ok": False,
            "live_read_verified": False,
            "message": "GOOGLE_ADS_CUSTOMER_ID and GOOGLE_ADS_DEVELOPER_TOKEN required.",
            "setup_url": "https://developers.google.com/google-ads/api/docs/start",
        }
    return {
        "ok": True,
        "live_read_verified": False,
        "message": "Credentials present — implement OAuth + google-ads library for live read/write.",
        "customer_id": customer_id,
        "blocked_by": "OAuth refresh token not stored in this release — use sandbox reporting manually.",
    }