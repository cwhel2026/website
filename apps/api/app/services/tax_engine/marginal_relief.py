from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


def corporation_tax_with_marginal_relief(taxable_profit_gbp: Decimal) -> dict:
    profit = max(Decimal("0"), taxable_profit_gbp)
    if profit <= ACTIVE_RULES.corporation_tax_lower_limit_gbp:
        rate = ACTIVE_RULES.corporation_tax_small_profits_rate_pct
        tax = (profit * rate / Decimal("100")).quantize(Decimal("0.01"))
        return {
            "taxable_profit_gbp": float(profit),
            "corporation_tax_gbp": float(tax),
            "effective_rate_pct": float(rate),
            "marginal_relief_applied": False,
            "rule_version": ACTIVE_RULES.version,
            "sources": ACTIVE_RULES.sources,
            "provisional": True,
            "requires_accountant_review": True,
        }

    if profit >= ACTIVE_RULES.corporation_tax_upper_limit_gbp:
        rate = ACTIVE_RULES.corporation_tax_main_rate_pct
        tax = (profit * rate / Decimal("100")).quantize(Decimal("0.01"))
        return {
            "taxable_profit_gbp": float(profit),
            "corporation_tax_gbp": float(tax),
            "effective_rate_pct": float(rate),
            "marginal_relief_applied": False,
            "rule_version": ACTIVE_RULES.version,
            "sources": ACTIVE_RULES.sources,
            "provisional": True,
            "requires_accountant_review": True,
        }

    main = ACTIVE_RULES.corporation_tax_main_rate_pct / Decimal("100")
    small = ACTIVE_RULES.corporation_tax_small_profits_rate_pct / Decimal("100")
    upper = ACTIVE_RULES.corporation_tax_upper_limit_gbp
    tax_at_main = profit * main
    marginal_fraction = (upper - profit) / upper
    relief = marginal_fraction * profit * (main - small)
    tax = (tax_at_main - relief).quantize(Decimal("0.01"))
    effective = (tax / profit * Decimal("100")).quantize(Decimal("0.01")) if profit else Decimal("0")
    return {
        "taxable_profit_gbp": float(profit),
        "corporation_tax_gbp": float(tax),
        "effective_rate_pct": float(effective),
        "marginal_relief_applied": True,
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "provisional": True,
        "requires_accountant_review": True,
    }