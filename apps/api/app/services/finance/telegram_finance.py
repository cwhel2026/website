"""Deterministic finance answers for Telegram — no invented figures."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance.engine import upcoming_reminders
from sqlalchemy import select

from app.models.company import CompanyProfile
from app.services.finance.cashflow import simple_cashflow_forecast
from app.services.finance.distributable_reserves import compute_distributable_reserves
from app.services.finance.financial_task_centre import task_centre_plain_summary
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
    if (("task" in lower and "finance" in lower) or lower.strip() in ("tasks", "what should i do", "to do")):
        return await task_centre_plain_summary(db)
    if "pay myself" in lower or ("salary" in lower and "dividend" in lower):
        reserves = await compute_distributable_reserves(db)
        if reserves.get("blocked") or not reserves.get("available"):
            return reserves.get("message", "Cannot recommend pay until FreeAgent reserves are verified.")
        profile = await db.execute(select(CompanyProfile).limit(1))
        prof = profile.scalar_one_or_none()
        desired = (
            prof.director_desired_monthly_net_gbp
            if prof and prof.director_desired_monthly_net_gbp
            else __import__("decimal").Decimal("2500")
        )
        dist = __import__("decimal").Decimal(str(reserves.get("after_tax_and_pending_dividends_gbp", 0)))
        tax = await compute_tax_reserves(db)
        profit = __import__("decimal").Decimal(str(tax.get("profit_estimate_gbp", 0)))
        opt = optimise_remuneration(
            RemunerationInputs(
                desired_monthly_net_gbp=desired,
                annual_company_profit_before_remuneration_gbp=profit,
                distributable_reserves_gbp=dist,
                company_cash_gbp=dist,
            )
        )
        if opt.get("blocked"):
            return opt.get("blocked_reason", opt.get("plain_english", "Blocked pending accountant review."))
        rec = opt.get("recommended")
        if not rec:
            return opt.get("plain_english", "Cannot compute pay yet.")
        p = rec["personal"]
        return (
            f"Planning for ~£{desired}/mo net (accountant must approve): "
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