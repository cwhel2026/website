"""Deterministic finance answers for Telegram — no invented figures."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance.engine import upcoming_reminders
from app.services.finance.cashflow import simple_cashflow_forecast
from app.services.finance.tax_reserves import compute_tax_reserves
from app.services.finance.watchdog import run_financial_watchdog
from app.services.remuneration.optimizer import RemunerationInputs, optimise_remuneration


async def proactive_finance_nudge(db: AsyncSession) -> str | None:
    issues = await run_financial_watchdog(db)
    high = [i for i in issues if i["severity"] == "high"]
    if not high:
        return None
    return "Heads up: " + high[0]["title"] + " — " + high[0]["detail"][:200]


async def answer_finance_question(db: AsyncSession, text: str) -> str | None:
    lower = text.lower()
    if "reserve" in lower and "tax" in lower:
        payload = await compute_tax_reserves(db)
        return (
            f"Tax reserve plan (provisional={payload['is_provisional']}): "
            f"£{payload['recommended_reserve_gbp']:.2f}. {payload['plain_english']}"
        )
    if "vat" in lower and "registration" in lower:
        payload = await compute_tax_reserves(db)
        vat = payload.get("vat_monitor") or {}
        return str(vat.get("plain_english", "VAT data unavailable."))
    if "deadline" in lower or "compliance" in lower:
        rows = await upcoming_reminders(db, within_days=60)
        if not rows:
            return "No statutory deadlines calculated — complete Company setup dates."
        lines = [f"• {r['title']}: {r['due_date']} ({r['days_left']} days)" for r in rows[:6]]
        return "Upcoming company obligations:\n" + "\n".join(lines)
    if "pay myself" in lower or "salary" in lower and "dividend" in lower:
        opt = optimise_remuneration(
            RemunerationInputs(
                desired_monthly_net_gbp=__import__("decimal").Decimal("2500"),
                annual_company_profit_before_remuneration_gbp=__import__("decimal").Decimal("60000"),
                distributable_reserves_gbp=__import__("decimal").Decimal("30000"),
                company_cash_gbp=__import__("decimal").Decimal("20000"),
            )
        )
        rec = opt.get("recommended")
        if not rec:
            return opt.get("plain_english", "Cannot compute pay yet.")
        p = rec["personal"]
        return (
            f"Example plan for ~£2500/mo net (needs accountant approval): "
            f"salary £{p['salary_gross_gbp']:.0f}/yr, dividends £{p['dividend_gbp']:.0f}/yr. "
            f"{opt['plain_english']}"
        )
    if "cash flow" in lower or "cashflow" in lower:
        fc = await simple_cashflow_forecast(db)
        return f"30-day forecast net £{fc['net_position_gbp']:.2f}. {fc['plain_english']}"
    if "problem" in lower or "watchdog" in lower or "alert" in lower:
        issues = await run_financial_watchdog(db)
        if not issues:
            return "No urgent financial alerts right now."
        return "Financial alerts:\n" + "\n".join(f"• [{i['severity']}] {i['title']}: {i['detail'][:120]}" for i in issues[:5])
    return None