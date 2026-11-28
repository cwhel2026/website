from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.finance.cashflow import multi_horizon_cashflow, simple_cashflow_forecast
from app.services.finance.distributable_reserves import compute_distributable_reserves
from app.services.finance.finance_security_audit import run_finance_security_audit
from app.services.finance.financial_task_centre import build_financial_tasks, task_centre_plain_summary
from app.services.finance.profitability import territory_profitability
from app.services.finance.financial_reports import (
    generate_annual_finance_report,
    generate_daily_finance_report,
    generate_monthly_finance_report,
    generate_weekly_finance_report,
)
from app.services.finance.freeagent_reports import distributable_profit_from_freeagent, sync_accounting_reports
from app.services.finance.payroll_freeagent import payroll_guidance, sync_payroll_status
from app.services.finance.watchdog import run_financial_watchdog
from sqlalchemy import select, func
from app.models.finance import BankTransaction, Receipt
from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.freeagent_cache import FinancialReportRecord
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


@router.post("/freeagent/reports/sync")
async def sync_fa_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await sync_accounting_reports(db)
    await db.commit()
    return result


@router.get("/freeagent/distributable-profit")
async def distributable_profit(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await distributable_profit_from_freeagent(db)


@router.get("/payroll/status")
async def payroll_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    data = await sync_payroll_status(db)
    await db.commit()
    data["guidance_doc"] = payroll_guidance()
    return data


@router.post("/reports/generate/{period}")
async def generate_report(
    period: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    if period == "daily":
        record = await generate_daily_finance_report(db)
    elif period == "weekly":
        record = await generate_weekly_finance_report(db)
    elif period == "monthly":
        record = await generate_monthly_finance_report(db)
    elif period == "annual":
        record = await generate_annual_finance_report(db)
    else:
        from fastapi import HTTPException
        raise HTTPException(400, "period must be daily|weekly|monthly|annual")
    await db.commit()
    return {"id": str(record.id), "period": record.period, "title": record.title}


@router.get("/reports/latest")
async def latest_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(
        select(FinancialReportRecord).order_by(FinancialReportRecord.generated_at.desc()).limit(10)
    )
    rows = list(result.scalars().all())
    return [
        {
            "id": str(r.id),
            "period": r.period,
            "title": r.title,
            "generated_at": r.generated_at.isoformat(),
            "dashboard_path": r.dashboard_path,
            "telegram_sent": r.telegram_sent,
        }
        for r in rows
    ]


@router.get("/cashflow")
async def cashflow(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 30,
) -> dict:
    if days in (7, 30, 90, 365):
        full = await multi_horizon_cashflow(db)
        return full["horizons"].get(str(days), await simple_cashflow_forecast(db, days=days))
    return await simple_cashflow_forecast(db, days=days)


@router.get("/cashflow/scenarios")
async def cashflow_scenarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await multi_horizon_cashflow(db)


@router.get("/distributable-reserves")
async def distributable_reserves(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    payload = await compute_distributable_reserves(db)
    await db.commit()
    return payload


@router.get("/tasks")
async def finance_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    tasks = await build_financial_tasks(db)
    return {"tasks": tasks, "summary": await task_centre_plain_summary(db)}


@router.get("/security-audit")
async def finance_security_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await run_finance_security_audit(db)

@router.get("/reconciliation")
async def reconciliation_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    async def count(model, *conditions):
        return int(await db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)

    return {
        "imported_bank_lines": await count(BankTransaction),
        "reconciled_bank_lines": await count(BankTransaction, BankTransaction.is_reconciled.is_(True), BankTransaction.is_duplicate.is_(False)),
        "unreconciled_bank_lines": await count(BankTransaction, BankTransaction.is_reconciled.is_(False), BankTransaction.is_duplicate.is_(False)),
        "flagged_duplicates": await count(BankTransaction, BankTransaction.is_duplicate.is_(True)),
        "receipts_without_bank_match": await count(Receipt, Receipt.matched_bank_transaction_id.is_(None)),
        "pending_reviews": await count(BookkeepingReviewItem, BookkeepingReviewItem.status == ReviewItemStatus.PENDING),
        "basis": "Local imported records only; not a verified bank balance or complete FreeAgent ledger.",
    }


@router.get("/reconciliation/payment-candidates")
async def payment_candidates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    from app.models.finance import Invoice, InvoiceStatus, SyncSource
    from app.services.analytics_service import issued_business_invoices

    rows = await db.execute(
        select(BankTransaction).where(
            BankTransaction.amount_gbp > 0,
            BankTransaction.is_reconciled.is_(False),
            BankTransaction.is_duplicate.is_(False),
            BankTransaction.matched_invoice_id.is_(None),
            BankTransaction.matched_expense_id.is_(None),
            BankTransaction.freeagent_explanation_url.is_(None),
        ).order_by(BankTransaction.transacted_at.desc(), BankTransaction.id).limit(100)
    )
    results = []
    for txn in rows.scalars().all():
        matches = await db.execute(
            select(Invoice).where(
                Invoice.id.in_(issued_business_invoices()),
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE]),
                Invoice.issue_date <= txn.transacted_at,
                Invoice.total_inc_vat_gbp - Invoice.amount_paid_gbp == txn.amount_gbp,
            ).order_by(Invoice.id).limit(2)
        )
        candidates = list(matches.scalars().all())
        results.append({
            "transaction_id": str(txn.id),
            "description": txn.description,
            "amount_gbp": str(txn.amount_gbp),
            "date": txn.transacted_at.isoformat(),
            "status": "unique_candidate" if len(candidates) == 1 else "ambiguous" if candidates else "unmatched",
            "invoice_id": str(candidates[0].id) if len(candidates) == 1 else None,
            "invoice_number": candidates[0].invoice_number if len(candidates) == 1 else None,
            "requires_review": True,
            "local_confirmation_allowed": len(candidates) == 1 and txn.source != SyncSource.FREEAGENT and not candidates[0].freeagent_id and not candidates[0].freeagent_url,
        })
    return {"transactions": results, "limit": 100, "basis": "Exact outstanding amount and invoice date only; suggestions are not verified payments."}
