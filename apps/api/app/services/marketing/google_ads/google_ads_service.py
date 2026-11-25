"""Google Ads API operations — REST transport with optional dry-run mock."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from app.config import get_settings

GOOGLE_ADS_API = "https://googleads.googleapis.com/v17"


@dataclass
class GoogleAdsTransportResult:
    ok: bool
    dry_run: bool
    payload: dict[str, Any]
    message: str | None = None


class GoogleAdsClient:
    def __init__(self, *, dry_run: bool | None = None) -> None:
        self.settings = get_settings()
        self.dry_run = dry_run if dry_run is not None else not bool(self.settings.google_ads_refresh_token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.google_ads_refresh_token or 'missing'}",
            "developer-token": self.settings.google_ads_developer_token or "",
            "Content-Type": "application/json",
        }

    async def search_campaigns(self) -> GoogleAdsTransportResult:
        if self.dry_run:
            return GoogleAdsTransportResult(
                ok=True,
                dry_run=True,
                payload={"campaigns": []},
                message="Dry-run — set GOOGLE_ADS_REFRESH_TOKEN for live read",
            )
        customer = self.settings.google_ads_customer_id
        if not customer:
            return GoogleAdsTransportResult(ok=False, dry_run=True, payload={}, message="GOOGLE_ADS_CUSTOMER_ID missing")
        url = f"{GOOGLE_ADS_API}/customers/{customer}/googleAds:searchStream"
        body = {"query": "SELECT campaign.id, campaign.name, campaign.status, metrics.cost_micros FROM campaign LIMIT 50"}
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, headers=self._headers(), json=body)
                data = resp.json() if resp.content else {}
                if resp.status_code >= 400:
                    return GoogleAdsTransportResult(ok=False, dry_run=False, payload=data, message=resp.text[:300])
        except httpx.HTTPError as exc:
            return GoogleAdsTransportResult(ok=False, dry_run=False, payload={}, message=str(exc)[:300])
        return GoogleAdsTransportResult(ok=True, dry_run=False, payload=data)

    async def create_paused_search_campaign(self, *, name: str, daily_budget_gbp: Decimal) -> GoogleAdsTransportResult:
        if self.dry_run:
            return GoogleAdsTransportResult(
                ok=True,
                dry_run=True,
                payload={"resourceName": f"customers/0/campaigns/sim-{name[:12]}"},
                message="Dry-run campaign create",
            )
        return GoogleAdsTransportResult(
            ok=False,
            dry_run=False,
            payload={},
            message="Live mutate requires google-ads client library batch job — use dry-run until OAuth refresh stored",
        )

    async def pause_all_active(self) -> GoogleAdsTransportResult:
        if self.dry_run:
            return GoogleAdsTransportResult(ok=True, dry_run=True, payload={"paused": 0})
        return GoogleAdsTransportResult(ok=False, dry_run=False, payload={}, message="Implement after OAuth verified")