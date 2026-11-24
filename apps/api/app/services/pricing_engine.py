import json
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import PricingProfile, PricingRule, PricingRuleType
from app.models.quotation import SurfaceCondition
from app.models.service import Service, ServiceCategory, SurfaceType
from app.models.territory import Territory


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
        .where(PricingProfile.is_active.is_(True))
        .order_by(PricingProfile.version.desc())
        .limit(1)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise ValueError("No active pricing profile configured")
    return profile


def _rule_amount(rules: list[PricingRule], rule_type: PricingRuleType) -> Decimal:
    for rule in rules:
        if rule.rule_type == rule_type and rule.is_active:
            return rule.amount_gbp
    return Decimal("0")


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

    rate_key = _rule_for_surface(rules, data.surface_type, data.service.category)
    base_rate = rate_key if rate_key > 0 else Decimal("18.00")
    condition_mult = CONDITION_MULTIPLIER[data.surface_condition]
    commercial_mult = Decimal("1.00")
    if data.service.is_commercial:
        commercial_mult = _rule_amount(rules, PricingRuleType.COMMERCIAL_MULTIPLIER) or Decimal(
            "1.25"
        )
        if commercial_mult < Decimal("1"):
            commercial_mult = Decimal("1.25")

    surface_subtotal = money(total_area * base_rate * condition_mult * commercial_mult)

    washing_charge = Decimal("0")
    if data.requires_washing and not data.customer_washed_already:
        wash_rate = _rule_amount(rules, PricingRuleType.WASHING_SURCHARGE) or Decimal("2.50")
        washing_charge = money(total_area * wash_rate)

    coating_charge = Decimal("0")
    if data.service.requires_coating:
        coat_rate = _rule_amount(rules, PricingRuleType.COATING_SURCHARGE) or Decimal("4.00")
        coating_charge = money(total_area * coat_rate)

    minimum_job = _rule_amount(rules, PricingRuleType.MINIMUM_JOB) or Decimal("250")
    territory_minimum = (
        data.territory.minimum_job_value_gbp if data.territory else Decimal("0")
    )
    effective_minimum = max(minimum_job, territory_minimum)

    subtotal_before_travel = surface_subtotal + washing_charge + coating_charge
    subtotal_before_travel = max(subtotal_before_travel, effective_minimum)

    travel = Decimal("0")
    if data.territory:
        per_km = data.territory.travel_cost_per_km_gbp
        base_travel = data.territory.base_travel_charge_gbp
        travel = money(base_travel + (data.distance_km_from_base * per_km * Decimal("2")))

    subtotal_ex_vat = money(subtotal_before_travel + travel)
    vat_rate = _rule_amount(rules, PricingRuleType.VAT_RATE) or Decimal("20")
    if vat_rate > Decimal("1"):
        vat_rate = vat_rate / Decimal("100")
    vat_gbp = money(subtotal_ex_vat * vat_rate)
    total_inc_vat = money(subtotal_ex_vat + vat_gbp)

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
    contribution = money(subtotal_ex_vat - total_cost)

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
        "lines": [
            {
                "label": "Surface restoration",
                "amount_gbp": float(surface_subtotal),
                "detail": f"{total_area} sqm @ {base_rate} x {condition_mult}",
            },
            {"label": "Washing", "amount_gbp": float(washing_charge)},
            {"label": "Coating", "amount_gbp": float(coating_charge)},
            {"label": "Minimum job adjustment", "minimum_gbp": float(effective_minimum)},
            {"label": "Travel", "amount_gbp": float(travel)},
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
        breakdown=breakdown,
        pricing_profile_id=profile.id,
        total_area_sqm=total_area,
    )


def _rule_for_surface(
    rules: list[PricingRule],
    surface: SurfaceType,
    category: ServiceCategory,
) -> Decimal:
    for rule in rules:
        if (
            rule.rule_type == PricingRuleType.PER_SQM
            and rule.is_active
            and rule.surface_type == surface
            and (rule.service_category is None or rule.service_category == category)
        ):
            return rule.amount_gbp
    for rule in rules:
        if rule.rule_type == PricingRuleType.PER_SQM and rule.is_active:
            return rule.amount_gbp
    return Decimal("0")