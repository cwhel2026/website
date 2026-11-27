from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.pricing import PricingProfile, PricingRule, PricingRuleType
from app.models.quotation import SurfaceCondition
from app.models.service import Service, ServiceCategory, SurfaceType
from app.models.territory import Territory
from app.services.pricing_engine import (
    PricingInput,
    QuotationSectionInput,
    _rule_for_surface,
    calculate_quotation,
    money,
)


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, item=None, items=None):
        self._item = item
        self._items = items or []

    def scalar_one_or_none(self):
        return self._item

    def scalars(self):
        return FakeScalars(self._items)


class FakeSession:
    def __init__(self, profile: PricingProfile):
        self.profile = profile

    async def execute(self, stmt):
        return FakeResult(item=self.profile)


def _profile_with_rules() -> PricingProfile:
    pid = uuid4()
    profile = PricingProfile(id=pid, name="test", version=1, is_active=True)
    profile.rules = [
        PricingRule(
            profile_id=pid,
            rule_type=PricingRuleType.PER_SQM,
            surface_type=SurfaceType.TARMAC,
            amount_gbp=Decimal("16.50"),
        ),
        PricingRule(
            profile_id=pid,
            rule_type=PricingRuleType.MINIMUM_JOB,
            amount_gbp=Decimal("250"),
        ),
        PricingRule(
            profile_id=pid,
            rule_type=PricingRuleType.WASHING_SURCHARGE,
            amount_gbp=Decimal("2.50"),
        ),
        PricingRule(
            profile_id=pid,
            rule_type=PricingRuleType.COATING_SURCHARGE,
            amount_gbp=Decimal("4.25"),
        ),
        PricingRule(
            profile_id=pid,
            rule_type=PricingRuleType.VAT_RATE,
            amount_gbp=Decimal("20"),
        ),
        PricingRule(
            profile_id=pid,
            rule_type=PricingRuleType.MIN_CONTRIBUTION_MARGIN,
            amount_gbp=Decimal("35"),
        ),
    ]
    return profile


def _service_restoration() -> Service:
    return Service(
        slug="tarmac-driveway-restoration",
        name="Tarmac driveway restoration",
        category=ServiceCategory.RESTORATION,
        requires_washing=True,
        requires_coating=True,
        is_commercial=False,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_minimum_job_charge_applied_for_small_area():
    db = FakeSession(_profile_with_rules())
    territory = Territory(
        code="A",
        name="West Lancashire",
        minimum_job_value_gbp=Decimal("250"),
        travel_cost_per_km_gbp=Decimal("0.45"),
        base_travel_charge_gbp=Decimal("0"),
    )
    result = await calculate_quotation(
        db,
        PricingInput(
            service=_service_restoration(),
            surface_type=SurfaceType.TARMAC,
            surface_condition=SurfaceCondition.GOOD,
            sections=[QuotationSectionInput("Main", Decimal("4"), Decimal("5"), Decimal("20"))],
            requires_washing=True,
            customer_washed_already=False,
            territory=territory,
            distance_km_from_base=Decimal("10"),
        ),
    )
    assert result.subtotal_ex_vat_gbp >= Decimal("250.00")
    assert result.vat_gbp == Decimal("0.00")
    assert result.vat_charged is False
    assert result.total_inc_vat_gbp % Decimal("5") == 0
    assert result.total_area_sqm == Decimal("20")


@pytest.mark.asyncio
async def test_condition_does_not_change_published_rate():
    db = FakeSession(_profile_with_rules())
    good = await calculate_quotation(
        db,
        PricingInput(
            service=_service_restoration(),
            surface_type=SurfaceType.TARMAC,
            surface_condition=SurfaceCondition.GOOD,
            sections=[QuotationSectionInput("Main", None, None, Decimal("50"))],
            requires_washing=False,
            customer_washed_already=True,
            territory=None,
            distance_km_from_base=Decimal("0"),
        ),
    )
    poor = await calculate_quotation(
        db,
        PricingInput(
            service=_service_restoration(),
            surface_type=SurfaceType.TARMAC,
            surface_condition=SurfaceCondition.POOR,
            sections=[QuotationSectionInput("Main", None, None, Decimal("50"))],
            requires_washing=False,
            customer_washed_already=True,
            territory=None,
            distance_km_from_base=Decimal("0"),
        ),
    )
    assert poor.subtotal_ex_vat_gbp == good.subtotal_ex_vat_gbp
    assert poor.breakdown["condition_recorded"] == "poor"


@pytest.mark.asyncio
async def test_two_visits_charge_two_return_journeys():
    db = FakeSession(_profile_with_rules())
    common = dict(
        service=_service_restoration(),
        surface_type=SurfaceType.TARMAC,
        surface_condition=SurfaceCondition.GOOD,
        sections=[QuotationSectionInput("Main", None, None, Decimal("80"))],
        territory=None,
        distance_km_from_base=Decimal("16.09344"),
    )
    two = await calculate_quotation(
        db,
        PricingInput(
            requires_washing=True,
            customer_washed_already=False,
            **common,
        ),
    )
    one = await calculate_quotation(
        db,
        PricingInput(
            requires_washing=False,
            customer_washed_already=True,
            **common,
        ),
    )
    assert two.breakdown["visits"] == 2
    assert one.breakdown["visits"] == 1
    assert two.estimated_travel_gbp == one.estimated_travel_gbp * 2


@pytest.mark.asyncio
async def test_total_rounds_up_to_five_pounds():
    db = FakeSession(_profile_with_rules())
    result = await calculate_quotation(
        db,
        PricingInput(
            service=_service_restoration(),
            surface_type=SurfaceType.TARMAC,
            surface_condition=SurfaceCondition.GOOD,
            sections=[QuotationSectionInput("Main", None, None, Decimal("40"))],
            requires_washing=False,
            customer_washed_already=True,
            territory=None,
            distance_km_from_base=Decimal("0"),
        ),
    )
    assert result.vat_gbp == Decimal("0.00")
    assert result.total_inc_vat_gbp % Decimal("5") == 0
    assert result.subtotal_ex_vat_gbp == result.total_inc_vat_gbp


@pytest.mark.asyncio
async def test_unconfigured_surface_is_refused():
    db = FakeSession(_profile_with_rules())
    with pytest.raises(ValueError, match="not configured"):
        await calculate_quotation(
            db,
            PricingInput(
                service=_service_restoration(),
                surface_type=SurfaceType.BLOCK_PAVING,
                surface_condition=SurfaceCondition.GOOD,
                sections=[QuotationSectionInput("Main", None, None, Decimal("40"))],
                requires_washing=False,
                customer_washed_already=True,
                territory=None,
                distance_km_from_base=Decimal("0"),
            ),
        )


@pytest.mark.asyncio
async def test_minimum_applies_before_travel():
    db = FakeSession(_profile_with_rules())
    result = await calculate_quotation(
        db,
        PricingInput(
            service=_service_restoration(),
            surface_type=SurfaceType.TARMAC,
            surface_condition=SurfaceCondition.GOOD,
            sections=[QuotationSectionInput("Main", None, None, Decimal("5"))],
            requires_washing=False,
            customer_washed_already=True,
            territory=None,
            distance_km_from_base=Decimal("0"),
        ),
    )
    minimum_line = next(
        line for line in result.breakdown["lines"] if line["label"] == "Minimum job adjustment"
    )
    assert Decimal(str(minimum_line["minimum_gbp"])) == Decimal("250")
    assert Decimal(str(minimum_line["amount_gbp"])) > 0
    assert result.estimated_travel_gbp == Decimal("0")


@pytest.mark.asyncio
async def test_vat_is_omitted_unless_the_company_is_registered():
    db = FakeSession(_profile_with_rules())
    payload = dict(
        service=_service_restoration(),
        surface_type=SurfaceType.TARMAC,
        surface_condition=SurfaceCondition.GOOD,
        sections=[QuotationSectionInput("Main", None, None, Decimal("40"))],
        requires_washing=False,
        customer_washed_already=True,
        territory=None,
        distance_km_from_base=Decimal("0"),
    )
    plain = await calculate_quotation(db, PricingInput(charge_vat=False, **payload))
    taxed = await calculate_quotation(
        db, PricingInput(charge_vat=True, vat_rate=Decimal("0.20"), **payload)
    )
    assert plain.vat_gbp == Decimal("0.00")
    assert plain.total_inc_vat_gbp == plain.subtotal_ex_vat_gbp == Decimal("830.00")
    assert taxed.subtotal_ex_vat_gbp == Decimal("830.00")
    assert taxed.vat_gbp == Decimal("166.00")
    assert taxed.total_inc_vat_gbp == Decimal("1000.00")
    assert taxed.breakdown["lines"][-1]["label"] == "Round up to £5"


def test_registered_rounding_happens_after_vat():
    from app.services.pricing_engine import round_up_to_nearest_five

    net = Decimal("674.80")
    vat = money(net * Decimal("0.20"))
    exact = money(net + vat)
    assert exact == Decimal("809.76")
    assert round_up_to_nearest_five(exact) == Decimal("810.00")
    assert round_up_to_nearest_five(net) == Decimal("675.00")


def test_money_rounding():
    assert money(Decimal("10.005")) == Decimal("10.01")


def test_rule_for_surface_prefers_matching_surface():
    rules = [
        PricingRule(
            rule_type=PricingRuleType.PER_SQM,
            surface_type=SurfaceType.TARMAC,
            amount_gbp=Decimal("16"),
            is_active=True,
        ),
        PricingRule(
            rule_type=PricingRuleType.PER_SQM,
            surface_type=SurfaceType.BLOCK_PAVING,
            amount_gbp=Decimal("14"),
            is_active=True,
        ),
    ]
    assert _rule_for_surface(rules, SurfaceType.BLOCK_PAVING, ServiceCategory.RESTORATION) == Decimal("14")