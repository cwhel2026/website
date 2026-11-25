"""Versioned UK Ltd tax constants — each pack lists HMRC/GOV.UK sources and verification dates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class IncomeTaxBands:
    name: str
    lower_from: Decimal
    upper_to: Decimal
    rate_pct: Decimal


@dataclass(frozen=True)
class TaxRulePack:
    version: str
    tax_year_label: str
    effective_from: str
    effective_to: str
    verified_on: str
    sources: tuple[str, ...]
    corporation_tax_main_rate_pct: Decimal
    corporation_tax_small_profits_rate_pct: Decimal
    corporation_tax_lower_limit_gbp: Decimal
    corporation_tax_upper_limit_gbp: Decimal
    personal_allowance_gbp: Decimal
    personal_allowance_taper_start_gbp: Decimal
    dividend_allowance_gbp: Decimal
    vat_registration_threshold_gbp: Decimal
    vat_registration_forward_months: int
    income_tax_bands: tuple[IncomeTaxBands, ...]
    dividend_tax_bands: tuple[IncomeTaxBands, ...]
    employer_ni_rate_pct: Decimal
    employee_ni_rate_pct: Decimal
    employee_ni_rate_above_uel_pct: Decimal
    ni_primary_threshold_weekly_gbp: Decimal
    ni_upper_earnings_limit_weekly_gbp: Decimal
    employment_allowance_annual_gbp: Decimal
    employment_allowance_eligible: bool
    director_ni_annual_method: bool
    notes: tuple[str, ...]


RULES_2025_26 = TaxRulePack(
    version="2025-26-verified-1",
    tax_year_label="2025-26",
    effective_from="2025-04-06",
    effective_to="2026-04-05",
    verified_on="2025-11-25",
    sources=(
        "https://www.gov.uk/government/publications/rates-and-allowances-corporation-tax",
        "https://www.gov.uk/income-tax-rates",
        "https://www.gov.uk/vat-registration/thresholds",
        "https://www.gov.uk/national-insurance-rates",
        "https://www.gov.uk/tax-on-dividends",
    ),
    corporation_tax_main_rate_pct=Decimal("25"),
    corporation_tax_small_profits_rate_pct=Decimal("19"),
    corporation_tax_lower_limit_gbp=Decimal("50000"),
    corporation_tax_upper_limit_gbp=Decimal("250000"),
    personal_allowance_gbp=Decimal("12570"),
    personal_allowance_taper_start_gbp=Decimal("100000"),
    dividend_allowance_gbp=Decimal("500"),
    vat_registration_threshold_gbp=Decimal("90000"),
    vat_registration_forward_months=12,
    income_tax_bands=(
        IncomeTaxBands("basic", Decimal("0"), Decimal("37700"), Decimal("20")),
        IncomeTaxBands("higher", Decimal("37700"), Decimal("125140"), Decimal("40")),
        IncomeTaxBands("additional", Decimal("125140"), Decimal("999999999"), Decimal("45")),
    ),
    dividend_tax_bands=(
        IncomeTaxBands("basic", Decimal("0"), Decimal("37700"), Decimal("8.75")),
        IncomeTaxBands("higher", Decimal("37700"), Decimal("125140"), Decimal("33.75")),
        IncomeTaxBands("additional", Decimal("125140"), Decimal("999999999"), Decimal("39.35")),
    ),
    employer_ni_rate_pct=Decimal("15"),
    employee_ni_rate_pct=Decimal("8"),
    employee_ni_rate_above_uel_pct=Decimal("2"),
    ni_primary_threshold_weekly_gbp=Decimal("242"),
    ni_upper_earnings_limit_weekly_gbp=Decimal("967"),
    employment_allowance_annual_gbp=Decimal("10500"),
    employment_allowance_eligible=False,
    director_ni_annual_method=True,
    notes=(
        "Planning software only — not HMRC filing.",
        "Associated companies and short accounting periods must be set explicitly on CT calls.",
        "Employment Allowance disabled by default for single-director companies — confirm eligibility.",
    ),
)


# 2026/27 figures per GOV.UK / HMRC publications at verification date (frozen PA, same CT thresholds).
RULES_2026_27 = TaxRulePack(
    version="2026-27-verified-1",
    tax_year_label="2026-27",
    effective_from="2026-04-06",
    effective_to="2027-04-05",
    verified_on="2025-11-25",
    sources=(
        "https://www.gov.uk/government/publications/rates-and-allowances-corporation-tax",
        "https://www.gov.uk/income-tax-rates",
        "https://www.gov.uk/vat-registration/thresholds",
        "https://www.gov.uk/national-insurance-rates",
        "https://www.gov.uk/tax-on-dividends",
    ),
    corporation_tax_main_rate_pct=Decimal("25"),
    corporation_tax_small_profits_rate_pct=Decimal("19"),
    corporation_tax_lower_limit_gbp=Decimal("50000"),
    corporation_tax_upper_limit_gbp=Decimal("250000"),
    personal_allowance_gbp=Decimal("12570"),
    personal_allowance_taper_start_gbp=Decimal("100000"),
    dividend_allowance_gbp=Decimal("500"),
    vat_registration_threshold_gbp=Decimal("90000"),
    vat_registration_forward_months=12,
    income_tax_bands=(
        IncomeTaxBands("basic", Decimal("0"), Decimal("37700"), Decimal("20")),
        IncomeTaxBands("higher", Decimal("37700"), Decimal("125140"), Decimal("40")),
        IncomeTaxBands("additional", Decimal("125140"), Decimal("999999999"), Decimal("45")),
    ),
    dividend_tax_bands=(
        IncomeTaxBands("basic", Decimal("0"), Decimal("37700"), Decimal("8.75")),
        IncomeTaxBands("higher", Decimal("37700"), Decimal("125140"), Decimal("33.75")),
        IncomeTaxBands("additional", Decimal("125140"), Decimal("999999999"), Decimal("39.35")),
    ),
    employer_ni_rate_pct=Decimal("15"),
    employee_ni_rate_pct=Decimal("8"),
    employee_ni_rate_above_uel_pct=Decimal("2"),
    ni_primary_threshold_weekly_gbp=Decimal("242"),
    ni_upper_earnings_limit_weekly_gbp=Decimal("967"),
    employment_allowance_annual_gbp=Decimal("10500"),
    employment_allowance_eligible=False,
    director_ni_annual_method=True,
    notes=RULES_2025_26.notes,
)

_RULE_PACKS: tuple[TaxRulePack, ...] = (RULES_2025_26, RULES_2026_27)


def uk_tax_year_start(d: date) -> date:
    if d.month > 4 or (d.month == 4 and d.day >= 6):
        return date(d.year, 4, 6)
    return date(d.year - 1, 4, 6)


def rules_for_date(as_of: date | None = None) -> TaxRulePack:
    d = as_of or date.today()
    for pack in reversed(_RULE_PACKS):
        start = date.fromisoformat(pack.effective_from)
        end = date.fromisoformat(pack.effective_to)
        if start <= d <= end:
            return pack
    return _RULE_PACKS[-1] if d > date.fromisoformat(_RULE_PACKS[-1].effective_from) else _RULE_PACKS[0]


def rules_for_tax_year(label: str) -> TaxRulePack | None:
    for pack in _RULE_PACKS:
        if pack.tax_year_label == label:
            return pack
    return None


def list_rule_packs() -> list[dict]:
    return [
        {
            "version": p.version,
            "tax_year_label": p.tax_year_label,
            "effective_from": p.effective_from,
            "effective_to": p.effective_to,
            "verified_on": p.verified_on,
            "sources": list(p.sources),
        }
        for p in _RULE_PACKS
    ]


# Backward-compatible default (evaluated at import — prefer rules_for_date() in new code).
ACTIVE_RULES = rules_for_date()