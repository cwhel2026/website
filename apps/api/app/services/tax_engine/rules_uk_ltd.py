"""Versioned UK Ltd tax rule constants — update from HMRC/GOV.UK; AI must not invent rates."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TaxRulePack:
    version: str
    effective_from: str
    sources: list[str]
    corporation_tax_main_rate_pct: Decimal
    corporation_tax_small_profits_rate_pct: Decimal
    personal_allowance_gbp: Decimal
    dividend_allowance_gbp: Decimal
    vat_registration_threshold_gbp: Decimal
    notes: list[str]


# FY starting April 2024 — verify with accountant before filing (HMRC CT rates).
RULES_2025_26 = TaxRulePack(
    version="2025-26-draft-1",
    effective_from="2025-04-06",
    sources=[
        "https://www.gov.uk/government/publications/rates-and-allowances-corporation-tax",
        "https://www.gov.uk/income-tax-rates",
        "https://www.gov.uk/vat-registration/thresholds",
    ],
    corporation_tax_main_rate_pct=Decimal("25"),
    corporation_tax_small_profits_rate_pct=Decimal("19"),
    personal_allowance_gbp=Decimal("12570"),
    dividend_allowance_gbp=Decimal("500"),
    vat_registration_threshold_gbp=Decimal("90000"),
    notes=[
        "Indicative planning constants only — not HMRC filing software.",
        "Marginal relief and associated companies not yet modelled in Phase A.",
    ],
)


ACTIVE_RULES = RULES_2025_26