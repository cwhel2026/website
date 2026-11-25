from decimal import Decimal

import pytest

from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.personal_tax import income_tax_on_non_dividend_income
from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


def test_small_profits_corporation_tax():
    r = corporation_tax_with_marginal_relief(Decimal("30000"))
    assert r["corporation_tax_gbp"] == pytest.approx(5700.0)
    assert r["marginal_relief_applied"] is False


def test_marginal_relief_mid_band():
    r = corporation_tax_with_marginal_relief(Decimal("100000"))
    assert r["marginal_relief_applied"] is True
    assert r["corporation_tax_gbp"] < 100000 * 0.25


def test_personal_allowance_income_tax():
    r = income_tax_on_non_dividend_income(Decimal("20000"))
    taxable = r["taxable_after_allowance_gbp"]
    assert taxable == max(0, 20000 - float(ACTIVE_RULES.personal_allowance_gbp))