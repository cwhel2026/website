from dataclasses import dataclass
from datetime import UTC, datetime

from app.config import get_settings
from app.models.marketing import AdPlatform, IntegrationState
from app.services.ad_adapters import integration_state_for

settings = get_settings()


@dataclass
class PlatformIntegrationStatus:
    platform: str
    state: str
    live_api_ready: bool
    blocker: str | None
    credentials_present: bool


def platform_status() -> list[PlatformIntegrationStatus]:
    rows = [
        _meta_status(),
        _google_ads_status(),
        _google_search_console_status(),
        _ga4_status(),
        _meta_conversions_status(),
    ]
    return rows


def _meta_status() -> PlatformIntegrationStatus:
    token = bool(settings.meta_access_token)
    account = bool(settings.meta_ad_account_id)
    state = integration_state_for(AdPlatform.META)
    blocker = None
    live = False
    if not token:
        blocker = "Set META_ACCESS_TOKEN"
    elif not account:
        blocker = "Set META_AD_ACCOUNT_ID"
    else:
        blocker = "Campaign create/report API paths not verified in production"
    return PlatformIntegrationStatus(
        platform="meta_marketing",
        state=state.value,
        live_api_ready=live,
        blocker=blocker,
        credentials_present=token and account,
    )


def _google_ads_status() -> PlatformIntegrationStatus:
    cust = bool(settings.google_ads_customer_id)
    dev = bool(settings.google_ads_developer_token)
    state = integration_state_for(AdPlatform.GOOGLE)
    blocker = "Set GOOGLE_ADS_CUSTOMER_ID and GOOGLE_ADS_DEVELOPER_TOKEN" if not (cust and dev) else "OAuth + campaign endpoints not implemented"
    return PlatformIntegrationStatus(
        platform="google_ads",
        state=state.value,
        live_api_ready=False,
        blocker=blocker,
        credentials_present=cust and dev,
    )


def _google_search_console_status() -> PlatformIntegrationStatus:
    return PlatformIntegrationStatus(
        platform="google_search_console",
        state=IntegrationState.NOT_CONFIGURED.value,
        live_api_ready=False,
        blocker="GSC service account / OAuth not configured",
        credentials_present=False,
    )


def _ga4_status() -> PlatformIntegrationStatus:
    return PlatformIntegrationStatus(
        platform="ga4",
        state=IntegrationState.NOT_CONFIGURED.value,
        live_api_ready=False,
        blocker="GA4 property id + measurement protocol not configured",
        credentials_present=False,
    )


def _meta_conversions_status() -> PlatformIntegrationStatus:
    token = bool(settings.meta_access_token)
    return PlatformIntegrationStatus(
        platform="meta_conversions_api",
        state=IntegrationState.SANDBOX.value if token else IntegrationState.NOT_CONFIGURED.value,
        live_api_ready=False,
        blocker=None if token else "Set META_ACCESS_TOKEN for server events",
        credentials_present=token,
    )


def integration_snapshot_json() -> dict:
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "platforms": [p.__dict__ for p in platform_status()],
        "simulation_default": settings.marketing_simulation_default,
    }