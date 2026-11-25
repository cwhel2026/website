from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.finance.cashflow import simple_cashflow_forecast
from app.services.finance.profitability import territory_profitability
from app.services.finance.watchdog import run_financial_watchdog
from app.services.notifications.outbox import enqueue_notification

router = APIRouter(prefix="/finance/insights", tags=["finance-insights"])


@router.get("/watchdog")
async def watchdog(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    issues = await run_financial_watchdog(db)
    return {"issues": issues, "count": len(issues)}


@router.post("/watchdog/notify")
async def watchdog_notify(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    issues = await run_financial_watchdog(db)
    high = [i for i in issues if i["severity"] in ("high", "medium")]
    if not high:
        return {"queued": 0}
    body = "\n".join(f"• {i['title']}: {i['detail'][:160]}" for i in high[:8])
    await enqueue_notification(
        db,
        channel="telegram",
        title="Financial watchdog",
        body=body,
        category="finance_watchdog",
        dedupe_key=f"watchdog:{__import__('datetime').date.today().isoformat()}",
        priority="high",
    )
    await db.commit()
    return {"queued": 1, "issues": len(high)}


@router.get("/job-profitability/territories")
async def job_profitability(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = await territory_profitability(db)
    return [
        {"territory_code": r.territory_code, "estimated_profit_gbp": float(r.estimated_profit_gbp)}
        for r in rows
    ]


@router.get("/cashflow")
async def cashflow(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 30,
) -> dict:
    return await simple_cashflow_forecast(db, days=days)