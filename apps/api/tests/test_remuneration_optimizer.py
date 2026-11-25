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


def test_cash_exceeds_reserves_still_bounded_by_reserves():
    result = optimise_remuneration(
        RemunerationInputs(
            desired_monthly_net_gbp=Decimal("2000"),
            annual_company_profit_before_remuneration_gbp=Decimal("20000"),
            distributable_reserves_gbp=Decimal("5000"),
            company_cash_gbp=Decimal("50000"),
        )
    )
    rec = result.get("recommended")
    if rec:
        assert rec["dividend_gbp"] <= 5000