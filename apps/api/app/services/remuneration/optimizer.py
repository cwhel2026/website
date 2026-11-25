"""Salary + dividend optimiser — combined company and personal tax (planning only)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.national_insurance import employee_ni_on_salary, employer_ni_on_salary
from app.services.tax_engine.personal_tax import dividend_tax, income_tax_on_non_dividend_income
from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


@dataclass
class RemunerationInputs:
    desired_monthly_net_gbp: Decimal
    annual_company_profit_before_remuneration_gbp: Decimal
    distributable_reserves_gbp: Decimal
    company_cash_gbp: Decimal
    other_personal_income_gbp: Decimal = Decimal("0")
    employer_pension_gbp: Decimal = Decimal("0")


def _monthly_net_from_salary_and_dividend(
    annual_salary: Decimal,
    annual_dividend: Decimal,
    other_income: Decimal,
) -> dict:
    salary = max(Decimal("0"), annual_salary)
    div = max(Decimal("0"), annual_dividend)
    emp_ni = employee_ni_on_salary(salary)
    ni = Decimal(str(emp_ni["employee_ni_gbp"]))
    taxable_salary = max(Decimal("0"), salary - ni)
    it = income_tax_on_non_dividend_income(taxable_salary + other_income)
    extra_salary_tax = income_tax_on_non_dividend_income(taxable_salary)
    salary_tax = Decimal(str(extra_salary_tax["income_tax_gbp"]))
    div_tax = dividend_tax(div, other_income_gbp=taxable_salary + other_income)
    dividend_tax_gbp = Decimal(str(div_tax["dividend_tax_gbp"]))
    take_home = salary - ni - salary_tax + div - dividend_tax_gbp
    employer = employer_ni_on_salary(salary)
    return {
        "annual_take_home_gbp": float(take_home),
        "monthly_take_home_gbp": float((take_home / 12).quantize(Decimal("0.01"))),
        "salary_gross_gbp": float(salary),
        "dividend_gbp": float(div),
        "income_tax_gbp": float(salary_tax),
        "dividend_tax_gbp": float(dividend_tax_gbp),
        "employee_ni_gbp": float(ni),
        "employer_ni_gbp": employer["employer_ni_gbp"],
    }


def _company_cost(salary: Decimal, employer_ni: float, profit_before: Decimal) -> dict:
    profit_after_salary = profit_before - salary - Decimal(str(employer_ni))
    ct = corporation_tax_with_marginal_relief(max(Decimal("0"), profit_after_salary))
    return {
        "profit_after_remuneration_gbp": float(max(Decimal("0"), profit_after_salary)),
        "corporation_tax_gbp": ct["corporation_tax_gbp"],
        "employer_ni_gbp": employer_ni,
        "total_company_cost_gbp": float(salary + Decimal(str(employer_ni)) + Decimal(str(ct["corporation_tax_gbp"]))),
    }


def optimise_remuneration(inputs: RemunerationInputs) -> dict:
    target_annual_net = inputs.desired_monthly_net_gbp * 12
    profit = max(Decimal("0"), inputs.annual_company_profit_before_remuneration_gbp)
    reserves = max(Decimal("0"), inputs.distributable_reserves_gbp)
    cash = max(Decimal("0"), inputs.company_cash_gbp)

    scenarios: list[dict] = []
    salary_cents = range(0, min(int(profit), 60000) + 1, 3000)
    for sal_int in salary_cents:
        salary = Decimal(sal_int)
        remaining_profit = profit - salary
        employer = employer_ni_on_salary(salary)
        emp_cost = salary + Decimal(str(employer["employer_ni_gbp"]))
        if emp_cost > profit:
            continue
        profit_after_pay = profit - emp_cost
        ct = corporation_tax_with_marginal_relief(max(Decimal("0"), profit_after_pay))
        after_ct = Decimal(str(profit_after_pay)) - Decimal(str(ct["corporation_tax_gbp"]))
        max_div = min(after_ct, reserves)
        if max_div > cash:
            max_div = min(max_div, cash)
        max_div = max(Decimal("0"), max_div)

        for div_int in (0, int(max_div // 2), int(max_div)):
            div = Decimal(div_int)
            if div > reserves:
                continue
            if div > after_ct:
                continue
            personal = _monthly_net_from_salary_and_dividend(salary, div, inputs.other_personal_income_gbp)
            diff = abs(Decimal(str(personal["annual_take_home_gbp"])) - target_annual_net)
            company = _company_cost(salary, personal["employer_ni_gbp"], profit)
            lawful_dividend = div <= reserves and div <= after_ct
            scenarios.append(
                {
                    "salary_gross_gbp": personal["salary_gross_gbp"],
                    "dividend_gbp": personal["dividend_gbp"],
                    "monthly_take_home_gbp": personal["monthly_take_home_gbp"],
                    "target_gap_gbp": float(diff),
                    "lawful_dividend": lawful_dividend,
                    "dividend_blocked_reason": (
                        None
                        if lawful_dividend
                        else "Distributable profit/reserves insufficient — not recommended."
                    ),
                    "personal": personal,
                    "company": company,
                }
            )

    scenarios.sort(key=lambda s: (s["target_gap_gbp"], -s["monthly_take_home_gbp"]))
    best = scenarios[0] if scenarios else None
    candidates = scenarios[:5]

    strategy_summary = []
    if best:
        if best["dividend_gbp"] == 0:
            strategy_summary.append("salary_heavy")
        elif best["salary_gross_gbp"] == 0:
            strategy_summary.append("dividend_heavy")
        else:
            strategy_summary.append("salary_and_dividend_blend")
    personal_reserve_hint = float(target_annual_net) * 0.25

    return {
        "recommended": best,
        "alternatives": candidates,
        "strategy_tags": strategy_summary,
        "personal_tax_reserve_hint_gbp": personal_reserve_hint,
        "inputs": {
            "desired_monthly_net_gbp": float(inputs.desired_monthly_net_gbp),
            "profit_gbp": float(profit),
            "distributable_reserves_gbp": float(reserves),
            "company_cash_gbp": float(cash),
            "warning_cash_not_profit": (
                "Bank cash is higher than distributable profit — dividends must follow profit, not cash."
                if cash > reserves
                else None
            ),
        },
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "requires_accountant_review": True,
        "provisional": True,
        "plain_english": (
            "These scenarios optimise estimated combined tax — approve with your accountant before payroll or dividends."
            if best
            else "Not enough company profit data to recommend pay — update accounts or company profile."
        ),
    }