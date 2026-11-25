from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import TaxRulePack, rules_for_date


def _prorated_limits(
    rules: TaxRulePack,
    *,
    associated_companies: int,
    accounting_period_months: int,
) -> tuple[Decimal, Decimal]:
    assoc = max(1, associated_companies)
    lower = rules.corporation_tax_lower_limit_gbp / Decimal(assoc)
    upper = rules.corporation_tax_upper_limit_gbp / Decimal(assoc)
    if accounting_period_months < 12:
        factor = Decimal(accounting_period_months) / Decimal("12")
        lower = (lower * factor).quantize(Decimal("0.01"))
        upper = (upper * factor).quantize(Decimal("0.01"))
    return lower, upper


def corporation_tax_with_marginal_relief(
    taxable_profit_gbp: Decimal,
    *,
    rules: TaxRulePack | None = None,
    associated_companies: int = 1,
    accounting_period_months: int = 12,
) -> dict:
    rules = rules or rules_for_date()
    profit = max(Decimal("0"), taxable_profit_gbp)
    lower, upper = _prorated_limits(
        rules,
        associated_companies=associated_companies,
        accounting_period_months=accounting_period_months,
    )

    if profit <= lower:
        rate = rules.corporation_tax_small_profits_rate_pct
        tax = (profit * rate / Decimal("100")).quantize(Decimal("0.01"))
        return _result(profit, tax, rate, False, rules, associated_companies, accounting_period_months, lower, upper)

    if profit >= upper:
        rate = rules.corporation_tax_main_rate_pct
        tax = (profit * rate / Decimal("100")).quantize(Decimal("0.01"))
        return _result(profit, tax, rate, False, rules, associated_companies, accounting_period_months, lower, upper)

    main = rules.corporation_tax_main_rate_pct / Decimal("100")
    small = rules.corporation_tax_small_profits_rate_pct / Decimal("100")
    tax_at_main = profit * main
    marginal_fraction = (upper - profit) / upper if upper > 0 else Decimal("0")
    relief = marginal_fraction * profit * (main - small)
    tax = (tax_at_main - relief).quantize(Decimal("0.01"))
    effective = (tax / profit * Decimal("100")).quantize(Decimal("0.01")) if profit else Decimal("0")
    return _result(profit, tax, effective, True, rules, associated_companies, accounting_period_months, lower, upper)


def _result(
    profit: Decimal,
    tax: Decimal,
    effective_rate: Decimal,
    marginal: bool,
    rules: TaxRulePack,
    associated_companies: int,
    months: int,
    lower: Decimal,
    upper: Decimal,
) -> dict:
    return {
        "taxable_profit_gbp": float(profit),
        "corporation_tax_gbp": float(tax),
        "effective_rate_pct": float(effective_rate),
        "marginal_relief_applied": marginal,
        "associated_companies": associated_companies,
        "accounting_period_months": months,
        "lower_limit_gbp": float(lower),
        "upper_limit_gbp": float(upper),
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "sources": list(rules.sources),
        "verified_on": rules.verified_on,
        "provisional": False,
        "requires_accountant_review": associated_companies > 1 or months != 12,
    }