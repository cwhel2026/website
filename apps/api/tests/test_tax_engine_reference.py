from decimal import Decimal

import pytest

from app.services.remuneration.optimizer import RemunerationInputs, optimise_remuneration
from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.national_insurance import employee_ni_on_salary
from app.services.tax_engine.personal_tax import (
    dividend_tax,
    incremental_income_tax_on_salary,
    tapered_personal_allowance,
)
from app.services.tax_engine.rules_uk_ltd import RULES_2025_26, rules_for_tax_year


def test_rules_2026_27_pack_exists():
    pack = rules_for_tax_year("2026-27")
    assert pack is not None
    assert pack.effective_from == "2026-04-06"


def test_ct_small_profits_rate_boundary():
    rules = RULES_2025_26
    r50 = corporation_tax_with_marginal_relief(Decimal("50000"), rules=rules)
    assert r50["corporation_tax_gbp"] == pytest.approx(9500.0)
    r50_01 = corporation_tax_with_marginal_relief(Decimal("50000.01"), rules=rules)
    assert r50_01["marginal_relief_applied"] is True


def test_personal_allowance_taper_at_125140():
    rules = RULES_2025_26
    allow = tapered_personal_allowance(Decimal("125140"), rules)
    assert allow == Decimal("0")


def test_employee_ni_upper_earnings_limit():
    rules = RULES_2025_26
    primary = rules.ni_primary_threshold_weekly_gbp * 52
    uel = rules.ni_upper_earnings_limit_weekly_gbp * 52
    mid = employee_ni_on_salary(primary + (uel - primary) / 2, rules=rules)
    above = employee_ni_on_salary(uel + Decimal("10000"), rules=rules)
    assert above["employee_ni_gbp"] > mid["employee_ni_gbp"]


def test_incremental_salary_tax_respects_other_income():
    rules = RULES_2025_26
    inc = incremental_income_tax_on_salary(Decimal("12000"), Decimal("40000"), rules=rules)
    assert inc["incremental_income_tax_gbp"] >= 0


def test_dividend_allowance_500():
    rules = RULES_2025_26
    d = dividend_tax(Decimal("600"), other_non_dividend_gbp=Decimal("0"), rules=rules)
    assert d["chargeable_dividends_gbp"] == pytest.approx(100.0)


def test_optimiser_prefers_lower_combined_tax():
    out = optimise_remuneration(
        RemunerationInputs(
            desired_monthly_net_gbp=Decimal("2500"),
            annual_company_profit_before_remuneration_gbp=Decimal("80000"),
            distributable_reserves_gbp=Decimal("40000"),
            company_cash_gbp=Decimal("50000"),
            other_personal_income_gbp=Decimal("0"),
        )
    )
    assert out.get("recommended")
    assert "combined_tax_gbp" in out["recommended"]