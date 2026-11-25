from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES, IncomeTaxBands


def income_tax_on_non_dividend_income(
    taxable_gbp: Decimal,
    *,
    personal_allowance: Decimal | None = None,
) -> dict:
    allowance = personal_allowance if personal_allowance is not None else ACTIVE_RULES.personal_allowance_gbp
    income = max(Decimal("0"), taxable_gbp)
    remaining = max(Decimal("0"), income - allowance)
    tax = Decimal("0")
    detail: list[dict] = []

    for band in ACTIVE_RULES.income_tax_bands:
        if remaining <= 0:
            break
        slice_gbp = min(remaining, band.upper_to - band.lower_from)
        if slice_gbp > 0:
            part = (slice_gbp * band.rate_pct / Decimal("100")).quantize(Decimal("0.01"))
            tax += part
            detail.append(
                {
                    "band": band.name,
                    "amount_gbp": float(slice_gbp),
                    "rate_pct": float(band.rate_pct),
                    "tax_gbp": float(part),
                }
            )
            remaining -= slice_gbp

    return {
        "taxable_after_allowance_gbp": float(max(Decimal("0"), income - allowance)),
        "income_tax_gbp": float(tax),
        "bands": detail,
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "provisional": True,
    }


def dividend_tax(
    dividend_gbp: Decimal,
    *,
    other_income_gbp: Decimal = Decimal("0"),
) -> dict:
    """Dividend allowance then tax rates by band — planning only."""
    div = max(Decimal("0"), dividend_gbp)
    allowance_used = min(div, ACTIVE_RULES.dividend_allowance_gbp)
    chargeable = max(Decimal("0"), div - allowance_used)
    if chargeable == 0:
        return {
            "dividend_tax_gbp": 0.0,
            "rule_version": ACTIVE_RULES.version,
            "sources": ACTIVE_RULES.sources,
            "provisional": True,
        }
    other = max(Decimal("0"), other_income_gbp)
    effective_income = other
    tax = Decimal("0")
    remaining_div = chargeable
    for band in ACTIVE_RULES.dividend_tax_bands:
        room = max(Decimal("0"), band.upper_to - max(effective_income, band.lower_from))
        slice_gbp = min(remaining_div, room)
        if slice_gbp > 0:
            tax += (slice_gbp * band.rate_pct / Decimal("100")).quantize(Decimal("0.01"))
            remaining_div -= slice_gbp
            effective_income += slice_gbp
    return {
        "dividend_tax_gbp": float(tax),
        "chargeable_dividends_gbp": float(chargeable),
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "provisional": True,
    }