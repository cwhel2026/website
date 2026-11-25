"""Constrained remuneration optimiser — deterministic tax engine only (planning, not payroll)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.national_insurance import employee_ni_on_salary, employer_ni_on_salary
from app.services.tax_engine.personal_tax import dividend_tax, incremental_income_tax_on_salary
from app.services.tax_engine.rules_uk_ltd import rules_for_date


@dataclass
class RemunerationInputs:
    desired_monthly_net_gbp: Decimal
    annual_company_profit_before_remuneration_gbp: Decimal
    distributable_reserves_gbp: Decimal
    company_cash_gbp: Decimal
    other_personal_income_gbp: Decimal = Decimal("0")
    employer_pension_gbp: Decimal = Decimal("0")
    obligation_reserve_gbp: Decimal = Decimal("0")
    associated_companies: int = 1
    accounting_period_months: int = 12


def _evaluate_scenario(
    inputs: RemunerationInputs,
    salary: Decimal,
    dividend: Decimal,
) -> dict | None:
    rules = rules_for_date()
    profit = max(Decimal("0"), inputs.annual_company_profit_before_remuneration_gbp)
    employer = employer_ni_on_salary(salary, rules=rules)
    employer_ni = Decimal(str(employer["employer_ni_gbp"]))
    payroll_cash = salary + employer_ni
    if payroll_cash > inputs.company_cash_gbp:
        return None
    if payroll_cash + inputs.obligation_reserve_gbp > inputs.company_cash_gbp:
        return None

    profit_after_pay = profit - payroll_cash
    if profit_after_pay < 0:
        return None

    ct = corporation_tax_with_marginal_relief(
        profit_after_pay,
        rules=rules,
        associated_companies=inputs.associated_companies,
        accounting_period_months=inputs.accounting_period_months,
    )
    corp_tax = Decimal(str(ct["corporation_tax_gbp"]))
    after_ct = profit_after_pay - corp_tax

    if dividend > after_ct or dividend > inputs.distributable_reserves_gbp:
        return None
    if dividend > inputs.company_cash_gbp - payroll_cash - inputs.obligation_reserve_gbp:
        return None

    emp_ni = Decimal(str(employee_ni_on_salary(salary, rules=rules)["employee_ni_gbp"]))
    inc = incremental_income_tax_on_salary(
        salary,
        inputs.other_personal_income_gbp,
        dividends_for_pa_taper_gbp=salary + dividend,
    )
    salary_tax = Decimal(str(inc["incremental_income_tax_gbp"]))
    div_tax_res = dividend_tax(
        dividend,
        other_non_dividend_gbp=inputs.other_personal_income_gbp + salary,
        dividends_for_pa_taper_gbp=dividend,
        rules=rules,
    )
    div_tax = Decimal(str(div_tax_res["dividend_tax_gbp"]))

    take_home = salary - emp_ni - salary_tax + dividend - div_tax
    personal_tax = salary_tax + div_tax + emp_ni
    combined_tax = personal_tax + corp_tax + employer_ni

    return {
        "salary_gross_gbp": float(salary),
        "dividend_gbp": float(dividend),
        "annual_take_home_gbp": float(take_home),
        "monthly_take_home_gbp": float((take_home / 12).quantize(Decimal("0.01"))),
        "personal_tax_gbp": float(personal_tax),
        "corporation_tax_gbp": float(corp_tax),
        "employer_ni_gbp": float(employer_ni),
        "combined_tax_gbp": float(combined_tax),
        "profit_after_remuneration_gbp": float(max(Decimal("0"), after_ct - dividend)),
        "lawful_dividend": dividend <= inputs.distributable_reserves_gbp and dividend <= after_ct,
        "personal": {
            "income_tax_gbp": float(salary_tax),
            "dividend_tax_gbp": float(div_tax),
            "employee_ni_gbp": float(emp_ni),
        },
        "company": {
            "corporation_tax_gbp": float(corp_tax),
            "employer_ni_gbp": float(employer_ni),
            "total_company_cost_gbp": float(payroll_cash + corp_tax + dividend),
        },
    }


def optimise_remuneration(inputs: RemunerationInputs) -> dict:
    rules = rules_for_date()
    target_annual = inputs.desired_monthly_net_gbp * 12
    tolerance = Decimal("600")
    profit_cap = int(min(inputs.annual_company_profit_before_remuneration_gbp, Decimal("150000")))
    if profit_cap < 0:
        profit_cap = 0

    scenarios: list[dict] = []
    salary_step = Decimal("500")
    for sal_int in range(0, profit_cap + 1, int(salary_step)):
        salary = Decimal(sal_int)
        div_cap = min(
            inputs.distributable_reserves_gbp,
            inputs.company_cash_gbp - inputs.obligation_reserve_gbp,
        )
        if div_cap < 0:
            div_cap = Decimal("0")
        max_div_int = int(div_cap)
        div_points = set(range(0, max_div_int + 1, int(salary_step)))
        if max_div_int not in div_points:
            div_points.add(max_div_int)
        for div_int in sorted(div_points):
            row = _evaluate_scenario(inputs, salary, Decimal(div_int))
            if row is None:
                continue
            gap = abs(Decimal(str(row["annual_take_home_gbp"])) - target_annual)
            if gap > tolerance:
                continue
            row["target_gap_gbp"] = float(gap)
            scenarios.append(row)

    if not scenarios:
        return {
            "blocked": True,
            "blocked_reason": "No lawful scenario meets cash, distributable reserves, and net income tolerance.",
            "requires_accountant_review": True,
            "rule_version": rules.version,
            "sources": list(rules.sources),
            "verified_on": rules.verified_on,
            "plain_english": "Cannot recommend pay — missing figures or constraints block all scenarios.",
        }

    scenarios.sort(key=lambda s: (s["combined_tax_gbp"], s["target_gap_gbp"]))
    best = scenarios[0]
    alts = scenarios[1:6]

    recommendation_reason = (
        f"Lowest combined company and personal tax (£{best['combined_tax_gbp']:.0f}) "
        f"while delivering ~£{best['monthly_take_home_gbp']:.0f}/mo net within £{tolerance}/yr tolerance."
    )

    return {
        "recommended": best,
        "alternatives": alts,
        "recommendation_reason": recommendation_reason,
        "inputs": {
            "desired_monthly_net_gbp": float(inputs.desired_monthly_net_gbp),
            "distributable_reserves_gbp": float(inputs.distributable_reserves_gbp),
            "company_cash_gbp": float(inputs.company_cash_gbp),
            "obligation_reserve_gbp": float(inputs.obligation_reserve_gbp),
        },
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "sources": list(rules.sources),
        "verified_on": rules.verified_on,
        "requires_accountant_review": True,
        "provisional": False,
        "plain_english": recommendation_reason + " Accountant must approve before payroll or dividends.",
    }