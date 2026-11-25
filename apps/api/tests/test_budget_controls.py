from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.marketing import AdPlatform
from app.services.marketing.budget_controls import validate_campaign_spend


@pytest.mark.asyncio
async def test_live_spend_blocked_by_default():
    policy = SimpleNamespace(
        live_paid_spend_approved=False,
        emergency_pause_all=False,
        daily_limit_gbp=Decimal("0"),
        weekly_limit_gbp=Decimal("0"),
        monthly_limit_gbp=Decimal("0"),
        meta_daily_limit_gbp=Decimal("0"),
        google_daily_limit_gbp=Decimal("0"),
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=policy)),
    )
    db.scalar = AsyncMock(return_value=0)
    gate = await validate_campaign_spend(
        db,
        platform=AdPlatform.META,
        daily_budget_gbp=Decimal("5"),
        simulation_only=False,
    )
    assert gate["allowed"] is False
    assert "not approved" in gate["reason"].lower()


@pytest.mark.asyncio
async def test_simulation_allowed_without_live_approval():
    policy = SimpleNamespace(
        live_paid_spend_approved=False,
        emergency_pause_all=False,
        daily_limit_gbp=Decimal("0"),
        weekly_limit_gbp=Decimal("0"),
        monthly_limit_gbp=Decimal("0"),
        meta_daily_limit_gbp=Decimal("0"),
        google_daily_limit_gbp=Decimal("0"),
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=policy)),
    )
    db.scalar = AsyncMock(return_value=0)
    gate = await validate_campaign_spend(
        db,
        platform=AdPlatform.META,
        daily_budget_gbp=Decimal("5"),
        simulation_only=True,
    )
    assert gate["allowed"] is True


@pytest.mark.asyncio
async def test_emergency_pause_blocks_all():
    policy = SimpleNamespace(
        live_paid_spend_approved=True,
        emergency_pause_all=True,
        daily_limit_gbp=Decimal("100"),
        weekly_limit_gbp=Decimal("0"),
        monthly_limit_gbp=Decimal("0"),
        meta_daily_limit_gbp=Decimal("100"),
        google_daily_limit_gbp=Decimal("100"),
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=policy)),
    )
    db.scalar = AsyncMock(return_value=0)
    gate = await validate_campaign_spend(
        db,
        platform=AdPlatform.META,
        daily_budget_gbp=Decimal("1"),
        simulation_only=True,
    )
    assert gate["allowed"] is False