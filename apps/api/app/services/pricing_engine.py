from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pricing import PricingProfile, PricingRule, PricingRuleType
from app.models.quotation import SurfaceCondition
from app.models.service import Service, ServiceCategory, SurfaceType
from app.models.territory import Territory


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def round_up_to_nearest_five(value: Decimal) -> Decimal:
    """Customer-facing total: round the VAT-inclusive figure up to the next £5."""
    step = Decimal("5")
    units = (value / step).to_integral_value(rounding=ROUND_CEILING)
    return units * step


# Specified travel rates used only when the active profile has no TRAVEL rule.
SPEC_TRAVEL_GBP_PER_MILE = Decimal("0.45")
SPEC_DRIVING_GBP_PER_HOUR = Decimal("25")
# Same planning speed the scheduler uses for drive-time estimates.
ASSUMED_SPEED_KMH = Decimal("45")
KM_PER_MILE = Decimal("1.609344")


def visit_count(*, requires_washing: bool, customer_washed_already: bool, requires_coating: bool) -> int:
    """Washing and coating are separate visits, each with its own return journey."""
    washing_visit = requires_washing and not customer_washed_already
    if washing_visit and requires_coating:
        return 2
    return 1


@dataclass
class QuotationSectionInput:
    label: str
    length_m: Decimal | None
    width_m: Decimal | None
    area_sqm: Decimal


@dataclass
class PricingInput:
    service: Service
    surface_type: SurfaceType
    surface_condition: SurfaceCondition
    sections: list[QuotationSectionInput]
    requires_washing: bool
    customer_washed_already: bool
    territory: Territory | None
    distance_km_from_base: Decimal
    # "launch" (£10/m² tarmac) or "standard" (£12/m²). Other surfaces need their own rules.
    pricing_tier: str = "launch"
    charge_vat: bool = False
    vat_rate: Decimal = Decimal("0")


@dataclass
class PricingResult:
    subtotal_ex_vat_gbp: Decimal
    vat_gbp: Decimal
    total_inc_vat_gbp: Decimal
    estimated_labour_hours: Decimal
    estimated_materials_gbp: Decimal
    estimated_travel_gbp: Decimal
    estimated_contribution_gbp: Decimal
    meets_minimum_margin: bool
    requires_approval: bool
    vat_charged: bool
    vat_rate_percent: Decimal
    breakdown: dict
    pricing_profile_id: UUID
    total_area_sqm: Decimal


CONDITION_MULTIPLIER = {
    SurfaceCondition.GOOD: Decimal("1.00"),
    SurfaceCondition.FAIR: Decimal("1.05"),
    SurfaceCondition.POOR: Decimal("1.15"),
    SurfaceCondition.HEAVILY_DEGRADED: Decimal("1.30"),
}

LABOUR_HOURS_PER_SQM = {
    ServiceCategory.RESTORATION: Decimal("0.035"),
    ServiceCategory.CLEANING: Decimal("0.022"),
    ServiceCategory.REPAIR: Decimal("0.055"),
    ServiceCategory.COMMERCIAL: Decimal("0.028"),
}

MATERIAL_COST_PER_SQM = {
    ServiceCategory.RESTORATION: Decimal("3.20"),
    ServiceCategory.CLEANING: Decimal("0.65"),
    ServiceCategory.REPAIR: Decimal("4.50"),
    ServiceCategory.COMMERCIAL: Decimal("2.80"),
}

DEFAULT_LABOUR_RATE = Decimal("42.00")


async def get_active_pricing_profile(db: AsyncSession) -> PricingProfile:
    result = await db.execute(
        select(PricingProfile)
        .options(selectinload(PricingProfile.rules))
        .where(PricingProfile.is_active.is_(True))
        .order_by(PricingProfile.version.desc())
        .limit(1)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise ValueError("No active pricing profile configured")
    return profile


def _is_active(rule: PricingRule) -> bool:
    return rule.is_active is not False


def _rule_amount(rules: list[PricingRule], rule_type: PricingRuleType) -> Decimal | None:
    for rule in rules:
        if rule.rule_type == rule_type and _is_active(rule):
            return rule.amount_gbp
    return None


def _travel_rates(rules: list[PricingRule]) -> tuple[Decimal, Decimal]:
    for rule in rules:
        if rule.rule_type == PricingRuleType.TRAVEL and _is_active(rule):
            per_mile = rule.amount_gbp if rule.amount_gbp > 0 else SPEC_TRAVEL_GBP_PER_MILE
            hourly = (
                rule.percentage
                if rule.percentage is not None and rule.percentage > 0
                else SPEC_DRIVING_GBP_PER_HOUR
            )
            return per_mile, hourly
    return SPEC_TRAVEL_GBP_PER_MILE, SPEC_DRIVING_GBP_PER_HOUR


async def calculate_quotation(
    db: AsyncSession, data: PricingInput
) -> PricingResult:
    profile = await get_active_pricing_profile(db)
    rules = list(profile.rules)
    if not rules:
        result = await db.execute(
            select(PricingRule).where(PricingRule.profile_id == profile.id)
        )
        rules = list(result.scalars().all())

    total_area = sum((s.area_sqm for s in data.sections), Decimal("0"))
    if total_area <= 0:
        raise ValueError("Total area must be greater than zero")

    tier = data.pricing_tier if data.pricing_tier in ("launch", "standard") else "launch"
    base_rate = _rule_for_surface(rules, data.surface_type, data.service.category, tier)
    if base_rate is None or base_rate <= 0:
        raise ValueError(
            f"Pricing for {data.surface_type.value} ({tier}) is not configured. "
            "Add an active per-m² rule before quoting this surface."
        )
    # Published £/m² rates are not inflated by condition. Condition stays on the quote record.
    condition_mult = Decimal("1.00")
    commercial_mult = Decimal("1.00")
    if data.service.is_commercial:
        configured = _rule_amount(rules, PricingRuleType.COMMERCIAL_MULTIPLIER)
        commercial_mult = configured if configured is not None and configured >= 1 else Decimal("1")

    surface_subtotal = money(total_area * base_rate * condition_mult * commercial_mult)

    washing_charge = Decimal("0")
    if data.requires_washing and not data.customer_washed_already:
        wash_rate = _rule_amount(rules, PricingRuleType.WASHING_SURCHARGE)
        if wash_rate is not None and wash_rate > 0:
            washing_charge = money(total_area * wash_rate)

    coating_charge = Decimal("0")
    if data.service.requires_coating:
        coat_rate = _rule_amount(rules, PricingRuleType.COATING_SURCHARGE)
        if coat_rate is not None and coat_rate > 0:
            coating_charge = money(total_area * coat_rate)

    minimum_job = _rule_amount(rules, PricingRuleType.MINIMUM_JOB)
    if minimum_job is None:
        raise ValueError("No minimum job charge configured on the active pricing profile")
    territory_minimum = (
        data.territory.minimum_job_value_gbp if data.territory else Decimal("0")
    )
    effective_minimum = max(minimum_job, territory_minimum)

    # Minimum applies to the works (surface + washing + coating) before travel.
    # Travel is added afterwards. This order is intentional and matches the previous engine.
    works_before_minimum = surface_subtotal + washing_charge + coating_charge
    minimum_adjustment = money(max(Decimal("0"), effective_minimum - works_before_minimum))
    subtotal_before_travel = works_before_minimum + minimum_adjustment

    visits = visit_count(
        requires_washing=data.requires_washing,
        customer_washed_already=data.customer_washed_already,
        requires_coating=bool(data.service.requires_coating),
    )
    per_mile, per_hour = _travel_rates(rules)
    miles_one_way = data.distance_km_from_base / KM_PER_MILE
    hours_one_way = (
        data.distance_km_from_base / ASSUMED_SPEED_KMH
        if data.distance_km_from_base > 0
        else Decimal("0")
    )
    legs = Decimal(visits * 2)
    mileage_charge = money(miles_one_way * per_mile * legs)
    driving_charge = money(hours_one_way * per_hour * legs)
    travel = money(mileage_charge + driving_charge)

    net_before_round = money(subtotal_before_travel + travel)
    # Round the amount the customer pays, after VAT when it applies.
    # Do not fold a VAT-inclusive uplift back into the net lines: that made
    # £600 + £74.80 + £0.24 fail to equal either £675 or £810.
    if data.charge_vat and data.vat_rate > 0:
        vat_gbp = money(net_before_round * data.vat_rate)
        exact_payable = money(net_before_round + vat_gbp)
        total_payable = round_up_to_nearest_five(exact_payable)
        rounding_uplift = money(total_payable - exact_payable)
        subtotal_ex_vat = net_before_round
        vat_charged = True
        vat_rate_percent = (data.vat_rate * Decimal("100")).quantize(Decimal("0.01"))
    else:
        total_payable = round_up_to_nearest_five(net_before_round)
        rounding_uplift = money(total_payable - net_before_round)
        subtotal_ex_vat = total_payable
        vat_gbp = Decimal("0.00")
        vat_charged = False
        vat_rate_percent = Decimal("0.00")
    total_inc_vat = total_payable

    labour_rate = Decimal("42")
    hours_per_sqm = LABOUR_HOURS_PER_SQM.get(
        data.service.category, Decimal("0.03")
    )
    labour_hours = money(total_area * hours_per_sqm + Decimal("0.75"))
    labour_cost = money(labour_hours * labour_rate)

    materials_per_sqm = MATERIAL_COST_PER_SQM.get(
        data.service.category, Decimal("2.50")
    )
    materials_cost = money(total_area * materials_per_sqm)
    if washing_charge > 0:
        materials_cost += money(total_area * Decimal("0.15"))
    if coating_charge > 0:
        materials_cost += money(total_area * Decimal("1.10"))

    total_cost = money(labour_cost + materials_cost + travel)
    revenue_ex_vat = money(total_payable - vat_gbp)
    contribution = money(revenue_ex_vat - total_cost)

    min_margin_pct = _rule_amount(rules, PricingRuleType.MIN_CONTRIBUTION_MARGIN) or Decimal(
        "35"
    )
    if min_margin_pct > Decimal("1"):
        min_margin_pct = min_margin_pct / Decimal("100")
    margin_ratio = (
        contribution / subtotal_ex_vat if subtotal_ex_vat > 0 else Decimal("0")
    )
    meets_margin = margin_ratio >= min_margin_pct

    requires_approval = not meets_margin or total_inc_vat >= Decimal("5000")

    breakdown = {
        "profile_id": str(profile.id),
        "profile_version": profile.version,
        "pricing_tier": tier,
        "condition_recorded": data.surface_condition.value,
        "condition_multiplier_not_applied": str(CONDITION_MULTIPLIER[data.surface_condition]),
        "rate_gbp_per_sqm": float(base_rate),
        "vat_charged": vat_charged,
        "vat_rate_percent": float(vat_rate_percent),
        "net_before_rounding_gbp": float(net_before_round),
        "customer_total_gbp": float(total_payable),
        "minimum_rule": (
            "Works subtotal is raised to the greater of the pricing-rule minimum "
            "and the territory minimum. Travel is added after that. "
            "The amount the customer pays is then rounded up to the next £5. "
            "VAT is added before that rounding only when the company is VAT registered "
            "on the pricing date."
        ),
        "visits": visits,
        "lines": [
            {
                "label": "Surface restoration",
                "amount_gbp": float(surface_subtotal),
                "detail": f"{total_area} sqm @ {base_rate} ({tier})",
            },
            {"label": "Washing", "amount_gbp": float(washing_charge)},
            {"label": "Coating", "amount_gbp": float(coating_charge)},
            {
                "label": "Minimum job adjustment",
                "amount_gbp": float(minimum_adjustment),
                "minimum_gbp": float(effective_minimum),
            },
            {
                "label": "Travel",
                "amount_gbp": float(travel),
                "mileage_gbp": float(mileage_charge),
                "driving_time_gbp": float(driving_charge),
                "return_journeys": int(legs / 2),
            },
            {"label": "Round up to £5", "amount_gbp": float(rounding_uplift)},
        ],
        "costs": {
            "labour_hours": float(labour_hours),
            "labour_gbp": float(labour_cost),
            "materials_gbp": float(materials_cost),
            "travel_gbp": float(travel),
        },
        "margin_ratio": float(margin_ratio),
        "min_margin_required": float(min_margin_pct),
    }

    return PricingResult(
        subtotal_ex_vat_gbp=subtotal_ex_vat,
        vat_gbp=vat_gbp,
        total_inc_vat_gbp=total_inc_vat,
        estimated_labour_hours=labour_hours,
        estimated_materials_gbp=materials_cost,
        estimated_travel_gbp=travel,
        estimated_contribution_gbp=contribution,
        meets_minimum_margin=meets_margin,
        requires_approval=requires_approval,
        vat_charged=vat_charged,
        vat_rate_percent=vat_rate_percent,
        breakdown=breakdown,
        pricing_profile_id=profile.id,
        total_area_sqm=total_area,
    )


def _rule_for_surface(
    rules: list[PricingRule],
    surface: SurfaceType,
    category: ServiceCategory,
    tier: str = "launch",
) -> Decimal | None:
    candidates = [
        rule
        for rule in rules
        if rule.rule_type == PricingRuleType.PER_SQM
        and _is_active(rule)
        and rule.surface_type == surface
        and (rule.service_category is None or rule.service_category == category)
    ]
    labeled = [rule for rule in candidates if (rule.label or "") == tier]
    if labeled:
        return labeled[0].amount_gbp
    if any(rule.label for rule in candidates):
        return None
    if candidates:
        return candidates[0].amount_gbp
    return None