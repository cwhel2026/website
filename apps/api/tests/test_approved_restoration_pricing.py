from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.pricing import PricingProfile, PricingRule, PricingRuleType
from app.models.quotation import SurfaceCondition
from app.models.service import Service, ServiceCategory, SurfaceType
from app.services.pricing_engine import PricingInput, QuotationSectionInput, calculate_quotation


@pytest.mark.asyncio
@pytest.mark.parametrize("slug,surface,label,rate,materials,expected", [
    ("tarmac-driveway-restoration", SurfaceType.TARMAC, "approved", "10", "1.50", "690"),
    ("block-paving-cleaning-sealing", SurfaceType.BLOCK_PAVING, "approved", "12", "2.51", "810"),
    ("imprinted-concrete-restoration", SurfaceType.IMPRINTED_CONCRETE, "approved-clear", "12", "3", "810"),
    ("imprinted-concrete-colour-restoration", SurfaceType.IMPRINTED_CONCRETE, "approved-colour", "14", "2.97", "930"),
])
@pytest.mark.parametrize("area", [10, 60, 100])
async def test_approved_restoration(monkeypatch, slug, surface, label, rate, materials, expected, area):
    profile = PricingProfile(id=uuid4(), name="surfacecoat-approved-restoration", version=3)
    profile.rules = [
        PricingRule(rule_type=PricingRuleType.PER_SQM, surface_type=surface, label=label,
                    amount_gbp=Decimal(rate), percentage=Decimal(materials)),
        PricingRule(rule_type=PricingRuleType.MINIMUM_JOB, amount_gbp=Decimal("350")),
        PricingRule(rule_type=PricingRuleType.TRAVEL, amount_gbp=Decimal(".45"), percentage=Decimal("25")),
    ]

    async def active(db):
        return profile

    monkeypatch.setattr("app.services.pricing_engine.get_active_pricing_profile", active)
    result = await calculate_quotation(None, PricingInput(
        service=Service(slug=slug, category=ServiceCategory.RESTORATION, requires_coating=True),
        surface_type=surface, surface_condition=SurfaceCondition.GOOD,
        sections=[QuotationSectionInput("Main", None, None, Decimal(area))],
        requires_washing=False, customer_washed_already=True, territory=None,
        distance_km_from_base=Decimal("32.18688"), driving_hours_one_way=Decimal(".5"),
    ))
    assert result.estimated_travel_gbp == Decimal("86")
    assert result.breakdown["visits"] == 2
    assert result.vat_gbp == 0
    assert result.estimated_materials_gbp == Decimal(materials) * area
    assert result.total_inc_vat_gbp % 5 == 0
    if area == 60:
        assert result.total_inc_vat_gbp == Decimal(expected)
    elif area == 10:
        assert result.total_inc_vat_gbp == Decimal("440")
    else:
        assert result.total_inc_vat_gbp == Decimal(rate) * area + 90
