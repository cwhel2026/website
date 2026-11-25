from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


def estimate_corporation_tax(
    taxable_profit_gbp: Decimal,
    *,
    uses_small_profits_rate: bool = False,
) -> dict:
    """Deterministic placeholder — marginal relief not yet implemented."""
    profit = max(Decimal("0"), taxable_profit_gbp)
    rate = (
        ACTIVE_RULES.corporation_tax_small_profits_rate_pct
        if uses_small_profits_rate
        else ACTIVE_RULES.corporation_tax_main_rate_pct
    )
    tax = (profit * rate / Decimal("100")).quantize(Decimal("0.01"))
    return {
        "taxable_profit_gbp": profit,
        "rate_pct": float(rate),
        "estimated_corporation_tax_gbp": tax,
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "confidence": "provisional",
        "requires_accountant_review": True,
    }