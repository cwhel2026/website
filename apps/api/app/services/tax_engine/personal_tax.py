from decimal import Decimal

from app.services.tax_engine.rules_uk_ltd import IncomeTaxBands, TaxRulePack, rules_for_date


def tapered_personal_allowance(adjusted_net_income_gbp: Decimal, rules: TaxRulePack) -> Decimal:
    """Personal allowance taper for adjusted net income over £100,000."""
    income = max(Decimal("0"), adjusted_net_income_gbp)
    allowance = rules.personal_allowance_gbp
    if income <= rules.personal_allowance_taper_start_gbp:
        return allowance
    reduction = ((income - rules.personal_allowance_taper_start_gbp) / Decimal("2")).quantize(Decimal("0.01"))
    return max(Decimal("0"), allowance - reduction)


def _tax_on_slice(remaining: Decimal, band: IncomeTaxBands) -> tuple[Decimal, Decimal]:
    if remaining <= 0:
        return Decimal("0"), Decimal("0")
    width = band.upper_to - band.lower_from
    slice_gbp = min(remaining, width)
    if slice_gbp <= 0:
        return Decimal("0"), Decimal("0")
    tax = (slice_gbp * band.rate_pct / Decimal("100")).quantize(Decimal("0.01"))
    return slice_gbp, tax


def income_tax_on_non_dividend_income(
    gross_non_dividend_gbp: Decimal,
    *,
    dividends_for_pa_taper_gbp: Decimal = Decimal("0"),
    personal_allowance: Decimal | None = None,
    rules: TaxRulePack | None = None,
) -> dict:
    """Income tax on employment and other non-dividend income (gross — not net of NI)."""
    rules = rules or rules_for_date()
    gross = max(Decimal("0"), gross_non_dividend_gbp)
    adj_net = gross + max(Decimal("0"), dividends_for_pa_taper_gbp)
    allowance = personal_allowance if personal_allowance is not None else tapered_personal_allowance(adj_net, rules)
    remaining = max(Decimal("0"), gross - allowance)
    tax = Decimal("0")
    detail: list[dict] = []
    band_cursor = Decimal("0")

    for band in rules.income_tax_bands:
        if remaining <= 0:
            break
        # Position in cumulative band stack including other income stacking
        slice_gbp, part = _tax_on_slice(remaining, band)
        if slice_gbp > 0:
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
            band_cursor += slice_gbp

    missing_allowance = allowance == Decimal("0") and adj_net > rules.personal_allowance_taper_start_gbp
    return {
        "gross_non_dividend_gbp": float(gross),
        "personal_allowance_gbp": float(allowance),
        "taxable_after_allowance_gbp": float(max(Decimal("0"), gross - allowance)),
        "income_tax_gbp": float(tax),
        "bands": detail,
        "allowance_fully_tapered": missing_allowance,
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "sources": list(rules.sources),
        "verified_on": rules.verified_on,
        "provisional": False,
    }


def incremental_income_tax_on_salary(
    annual_salary_gbp: Decimal,
    other_non_dividend_gbp: Decimal,
    *,
    dividends_for_pa_taper_gbp: Decimal = Decimal("0"),
    rules: TaxRulePack | None = None,
) -> dict:
    """Income tax attributable to director salary given existing personal income."""
    rules = rules or rules_for_date()
    other = max(Decimal("0"), other_non_dividend_gbp)
    salary = max(Decimal("0"), annual_salary_gbp)
    without = income_tax_on_non_dividend_income(other, dividends_for_pa_taper_gbp=dividends_for_pa_taper_gbp, rules=rules)
    combined = income_tax_on_non_dividend_income(
        other + salary,
        dividends_for_pa_taper_gbp=dividends_for_pa_taper_gbp,
        rules=rules,
    )
    incremental = Decimal(str(combined["income_tax_gbp"])) - Decimal(str(without["income_tax_gbp"]))
    return {
        "incremental_income_tax_gbp": float(max(Decimal("0"), incremental)),
        "total_income_tax_gbp": combined["income_tax_gbp"],
        "rule_version": rules.version,
    }


def dividend_tax(
    dividend_gbp: Decimal,
    *,
    other_non_dividend_gbp: Decimal = Decimal("0"),
    dividends_for_pa_taper_gbp: Decimal | None = None,
    rules: TaxRulePack | None = None,
) -> dict:
    rules = rules or rules_for_date()
    div = max(Decimal("0"), dividend_gbp)
    allowance_used = min(div, rules.dividend_allowance_gbp)
    chargeable = max(Decimal("0"), div - allowance_used)
    if chargeable == 0:
        return {
            "dividend_tax_gbp": 0.0,
            "chargeable_dividends_gbp": 0.0,
            "rule_version": rules.version,
            "tax_year_label": rules.tax_year_label,
            "sources": list(rules.sources),
            "verified_on": rules.verified_on,
            "provisional": False,
        }

    other = max(Decimal("0"), other_non_dividend_gbp)
    tapered = dividends_for_pa_taper_gbp if dividends_for_pa_taper_gbp is not None else div
    _ = tapered_personal_allowance(other + tapered, rules)

    # Dividends sit above non-dividend income in the income stack for band purposes.
    effective_stack = other
    tax = Decimal("0")
    remaining_div = chargeable
    for band in rules.dividend_tax_bands:
        band_base = max(effective_stack, band.lower_from)
        room = max(Decimal("0"), band.upper_to - band_base)
        slice_gbp = min(remaining_div, room)
        if slice_gbp > 0:
            tax += (slice_gbp * band.rate_pct / Decimal("100")).quantize(Decimal("0.01"))
            remaining_div -= slice_gbp
            effective_stack += slice_gbp
        if remaining_div <= 0:
            break

    return {
        "dividend_tax_gbp": float(tax),
        "chargeable_dividends_gbp": float(chargeable),
        "dividend_allowance_used_gbp": float(allowance_used),
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "sources": list(rules.sources),
        "verified_on": rules.verified_on,
        "provisional": False,
    }