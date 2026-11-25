from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import TaxRulePack, rules_for_date


def _annual_thresholds(rules: TaxRulePack) -> tuple[Decimal, Decimal]:
    primary = rules.ni_primary_threshold_weekly_gbp * Decimal("52")
    uel = rules.ni_upper_earnings_limit_weekly_gbp * Decimal("52")
    return primary, uel


def employee_ni_on_salary(
    annual_gross_gbp: Decimal,
    *,
    rules: TaxRulePack | None = None,
    director_annual_method: bool | None = None,
) -> dict:
    rules = rules or rules_for_date()
    annual = max(Decimal("0"), annual_gross_gbp)
    use_director = rules.director_ni_annual_method if director_annual_method is None else director_annual_method
    primary, uel = _annual_thresholds(rules)
    if annual <= primary:
        return {
            "employee_ni_gbp": 0.0,
            "chargeable_gbp": 0.0,
            "rule_version": rules.version,
            "director_annual_method": use_director,
            "provisional": False,
        }
    band_main = min(annual, uel) - primary
    band_upper = max(Decimal("0"), annual - uel)
    ni_main = (max(Decimal("0"), band_main) * rules.employee_ni_rate_pct / Decimal("100")).quantize(Decimal("0.01"))
    ni_upper = (band_upper * rules.employee_ni_rate_above_uel_pct / Decimal("100")).quantize(Decimal("0.01"))
    total = ni_main + ni_upper
    return {
        "employee_ni_gbp": float(total),
        "chargeable_main_gbp": float(max(Decimal("0"), band_main)),
        "chargeable_upper_gbp": float(band_upper),
        "rate_main_pct": float(rules.employee_ni_rate_pct),
        "rate_upper_pct": float(rules.employee_ni_rate_above_uel_pct),
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "director_annual_method": use_director,
        "provisional": False,
    }


def employer_ni_on_salary(
    annual_gross_gbp: Decimal,
    *,
    rules: TaxRulePack | None = None,
    employment_allowance_applies: bool = False,
) -> dict:
    rules = rules or rules_for_date()
    annual = max(Decimal("0"), annual_gross_gbp)
    primary, _ = _annual_thresholds(rules)
    chargeable = max(Decimal("0"), annual - primary)
    ni = (chargeable * rules.employer_ni_rate_pct / Decimal("100")).quantize(Decimal("0.01"))
    allowance_used = Decimal("0")
    if employment_allowance_applies and rules.employment_allowance_eligible:
        allowance_used = min(ni, rules.employment_allowance_annual_gbp)
        ni -= allowance_used
    elif employment_allowance_applies and not rules.employment_allowance_eligible:
        return {
            "employer_ni_gbp": float(ni),
            "employment_allowance_applied_gbp": 0.0,
            "employment_allowance_blocked": True,
            "rule_version": rules.version,
            "requires_accountant_review": True,
            "provisional": False,
        }
    return {
        "employer_ni_gbp": float(max(Decimal("0"), ni)),
        "employment_allowance_applied_gbp": float(allowance_used),
        "chargeable_gbp": float(chargeable),
        "rate_pct": float(rules.employer_ni_rate_pct),
        "rule_version": rules.version,
        "provisional": False,
    }