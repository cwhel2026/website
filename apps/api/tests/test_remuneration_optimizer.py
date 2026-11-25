from decimal import Decimal

from app.services.remuneration.optimizer import RemunerationInputs, optimise_remuneration


def test_optimiser_returns_recommendation():
    result = optimise_remuneration(
        RemunerationInputs(
            desired_monthly_net_gbp=Decimal("3000"),
            annual_company_profit_before_remuneration_gbp=Decimal("80000"),
            distributable_reserves_gbp=Decimal("40000"),
            company_cash_gbp=Decimal("50000"),
        )
    )
    assert result["recommended"] is not None
    assert result["requires_accountant_review"] is True


def test_high_cash_low_reserves_warning():
    result = optimise_remuneration(
        RemunerationInputs(
            desired_monthly_net_gbp=Decimal("2000"),
            annual_company_profit_before_remuneration_gbp=Decimal("20000"),
            distributable_reserves_gbp=Decimal("5000"),
            company_cash_gbp=Decimal("50000"),
        )
    )
    assert result["inputs"]["warning_cash_not_profit"]