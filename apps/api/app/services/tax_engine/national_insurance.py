from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


def employer_ni_on_salary(annual_gross_gbp: Decimal) -> dict:
    """Simplified employer Class 1 secondary — no Employment Allowance modelling."""
    annual = max(Decimal("0"), annual_gross_gbp)
    secondary_threshold = ACTIVE_RULES.employee_ni_primary_threshold_weekly_gbp * Decimal("52")
    chargeable = max(Decimal("0"), annual - secondary_threshold)
    ni = (chargeable * ACTIVE_RULES.employer_ni_rate_pct / Decimal("100")).quantize(Decimal("0.01"))
    return {
        "employer_ni_gbp": float(ni),
        "chargeable_gbp": float(chargeable),
        "rate_pct": float(ACTIVE_RULES.employer_ni_rate_pct),
        "rule_version": ACTIVE_RULES.version,
        "provisional": True,
        "requires_accountant_review": True,
    }


def employee_ni_on_salary(annual_gross_gbp: Decimal) -> dict:
    annual = max(Decimal("0"), annual_gross_gbp)
    threshold = ACTIVE_RULES.employee_ni_primary_threshold_weekly_gbp * Decimal("52")
    chargeable = max(Decimal("0"), annual - threshold)
    ni = (chargeable * ACTIVE_RULES.employee_ni_rate_pct / Decimal("100")).quantize(Decimal("0.01"))
    return {
        "employee_ni_gbp": float(ni),
        "chargeable_gbp": float(chargeable),
        "rate_pct": float(ACTIVE_RULES.employee_ni_rate_pct),
        "rule_version": ACTIVE_RULES.version,
        "provisional": True,
    }