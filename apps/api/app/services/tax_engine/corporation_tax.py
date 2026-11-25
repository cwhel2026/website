from decimal import Decimal

from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief


def estimate_corporation_tax(
    taxable_profit_gbp: Decimal,
    *,
    uses_small_profits_rate: bool = False,
) -> dict:
    """Delegates to marginal relief engine (legacy query param ignored)."""
    del uses_small_profits_rate
    result = corporation_tax_with_marginal_relief(taxable_profit_gbp)
    return {
        "taxable_profit_gbp": result["taxable_profit_gbp"],
        "estimated_corporation_tax_gbp": Decimal(str(result["corporation_tax_gbp"])),
        "rule_version": result["rule_version"],
        "sources": result["sources"],
        "marginal_relief_applied": result.get("marginal_relief_applied"),
        "confidence": "provisional",
        "requires_accountant_review": True,
    }