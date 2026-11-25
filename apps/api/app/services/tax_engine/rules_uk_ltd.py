"""Versioned UK Ltd tax rule constants — update from HMRC/GOV.UK; AI must not invent rates."""

from dataclasses import dataclass
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
    effective_from: str
    sources: list[str]
    corporation_tax_main_rate_pct: Decimal
    corporation_tax_small_profits_rate_pct: Decimal
    corporation_tax_lower_limit_gbp: Decimal
    corporation_tax_upper_limit_gbp: Decimal
    personal_allowance_gbp: Decimal
    dividend_allowance_gbp: Decimal
    vat_registration_threshold_gbp: Decimal
    income_tax_bands: tuple[IncomeTaxBands, ...]
    dividend_tax_bands: tuple[IncomeTaxBands, ...]
    employer_ni_rate_pct: Decimal
    employee_ni_rate_pct: Decimal
    employee_ni_primary_threshold_weekly_gbp: Decimal
    notes: list[str]


# England/Wales/NI 2025-26 planning figures — confirm against HMRC before filing.
RULES_2025_26 = TaxRulePack(
    version="2025-26-draft-2",
    effective_from="2025-04-06",
    sources=[
        "https://www.gov.uk/government/publications/rates-and-allowances-corporation-tax",
        "https://www.gov.uk/income-tax-rates",
        "https://www.gov.uk/vat-registration/thresholds",
        "https://www.gov.uk/national-insurance-rates",
    ],
    corporation_tax_main_rate_pct=Decimal("25"),
    corporation_tax_small_profits_rate_pct=Decimal("19"),
    corporation_tax_lower_limit_gbp=Decimal("50000"),
    corporation_tax_upper_limit_gbp=Decimal("250000"),
    personal_allowance_gbp=Decimal("12570"),
    dividend_allowance_gbp=Decimal("500"),
    vat_registration_threshold_gbp=Decimal("90000"),
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
    employee_ni_primary_threshold_weekly_gbp=Decimal("242"),
    notes=[
        "Indicative planning constants only — not HMRC filing software.",
        "Marginal relief uses simplified model; associated companies not included.",
        "Employment Allowance and director NI annual method require accountant review.",
    ],
)


ACTIVE_RULES = RULES_2025_26