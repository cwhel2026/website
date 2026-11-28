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
        if payload.get("recommended_reserve_gbp") is None:
            return "Tax reserve unknown until reconciliation is complete."
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
        return "Verified available company cash and accountant review required before recommending director pay."
    if "cash flow" in lower or "cashflow" in lower:
        fc = await simple_cashflow_forecast(db)
        if fc.get("net_position_gbp") is None:
            return "Cashflow forecast unavailable until financial records are complete."
        return f"30-day forecast net £{fc['net_position_gbp']:.2f}. {fc['plain_english']}"
    if "problem" in lower or "watchdog" in lower or "alert" in lower:
        issues = await run_financial_watchdog(db)
        if not issues:
            return "No urgent financial alerts right now."
        return "Financial alerts:\n" + "\n".join(f"• [{i['severity']}] {i['title']}: {i['detail'][:120]}" for i in issues[:5])
    return None