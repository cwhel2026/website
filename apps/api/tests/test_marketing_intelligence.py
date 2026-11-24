from decimal import Decimal

import pytest

from app.models.marketing import AdPlatform, RegionalCampaign
from app.services.ad_adapters import launch_campaign
from app.services.marketing_intelligence import (
    check_budget_headroom,
    commercial_lead_score,
    propose_regional_campaigns,
    TerritoryCapacityInsight,
)


def test_commercial_lead_score_commercial_category():
    score = commercial_lead_score(
        has_email=True,
        has_postcode=True,
        category="Retail car park",
        territory_efficient=True,
    )
    assert score >= 70


@pytest.mark.asyncio
async def test_budget_monthly_limit():
    campaign = RegionalCampaign(
        name="test",
        platform=AdPlatform.META,
        daily_budget_gbp=Decimal("10"),
        monthly_budget_gbp=Decimal("100"),
        spent_gbp=Decimal("95"),
    )
    ok, msg = await check_budget_headroom(campaign, Decimal("10"))
    assert ok is False
    assert "monthly" in msg.lower()


def test_simulated_launch_always_safe():
    c = RegionalCampaign(name="t", platform=AdPlatform.META, simulation_only=True)
    r = launch_campaign(c, Decimal("5"))
    assert r.success and r.simulation


def test_proposals_skip_full_diary():
    insights = [
        TerritoryCapacityInsight(
            territory_id="1",
            territory_code="H",
            territory_name="Manchester",
            appointments_next_14_days=12,
            spare_capacity_score=0,
            recommendation="Pause",
            suggest_advertising=False,
        )
    ]
    assert propose_regional_campaigns(insights) == []