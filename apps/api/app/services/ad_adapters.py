from dataclasses import dataclass
from decimal import Decimal

from app.config import get_settings
from app.models.marketing import AdPlatform, IntegrationState, RegionalCampaign

settings = get_settings()


@dataclass
class AdapterResult:
    success: bool
    simulation: bool
    message: str
    external_id: str | None = None


def integration_state_for(platform: AdPlatform) -> IntegrationState:
    if platform == AdPlatform.META:
        token = getattr(settings, "meta_access_token", None) or ""
        if not token:
            return IntegrationState.NOT_CONFIGURED
        return IntegrationState.SANDBOX
    if platform == AdPlatform.GOOGLE:
        if not getattr(settings, "google_ads_customer_id", None):
            return IntegrationState.NOT_CONFIGURED
        return IntegrationState.SANDBOX
    return IntegrationState.NOT_CONFIGURED


async def fetch_campaign_metrics(campaign: RegionalCampaign) -> AdapterResult:
    """Reporting path — Meta insights when credentials verified."""
    state = integration_state_for(campaign.platform)
    if state == IntegrationState.NOT_CONFIGURED:
        return AdapterResult(False, False, "Integration not configured", None)
    if campaign.platform == AdPlatform.META:
        from app.services.marketing.meta_ads_client import fetch_account_insights

        data = await fetch_account_insights()
        if data.get("live_read_verified"):
            return AdapterResult(
                True,
                False,
                f"Account insights spend (7d): £{data.get('spend_gbp', 0):.2f}",
                None,
            )
        return AdapterResult(False, False, data.get("message", "Meta insights unavailable"))
    return AdapterResult(
        False,
        False,
        "Live reporting not verified for this platform.",
    )


def launch_campaign(campaign: RegionalCampaign, spend_cap: Decimal) -> AdapterResult:
    """Never calls external APIs unless explicitly verified connected — simulation by default."""
    if campaign.simulation_only:
        return AdapterResult(
            True,
            True,
            f"Simulated launch for {campaign.platform.value}: no real spend.",
            external_id=f"sim-{campaign.id}",
        )
    state = integration_state_for(campaign.platform)
    if state == IntegrationState.NOT_CONFIGURED:
        return AdapterResult(
            False,
            False,
            f"{campaign.platform.value} integration not configured — enable simulation or connect credentials.",
        )
    if spend_cap > campaign.daily_budget_gbp:
        return AdapterResult(False, False, "Spend cap exceeds daily budget limit.")
    return AdapterResult(
        False,
        False,
        "Live launch not implemented — credentials must be verified before production API calls.",
    )