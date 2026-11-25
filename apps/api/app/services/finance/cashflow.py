from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, Invoice, InvoiceStatus, Payment


async def simple_cashflow_forecast(db: AsyncSession, *, days: int = 30) -> dict:
    today = date.today()
    horizon = today + timedelta(days=days)

    inv = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE]),
            Invoice.due_date <= horizon,
        )
    )
    inflows = Decimal("0")
    for row in inv.scalars().all():
        inflows += row.total_inc_vat_gbp - row.amount_paid_gbp

    exp = await db.execute(select(Expense).where(Expense.expense_date <= horizon))
    outflows = sum((e.amount_gbp for e in exp.scalars().all()), Decimal("0"))

    pay = await db.execute(select(Payment))
    collected_recent = sum((p.amount_gbp for p in pay.scalars().all()), Decimal("0"))

    net = inflows - outflows
    return {
        "horizon_days": days,
        "expected_inflows_gbp": float(inflows),
        "known_outflows_gbp": float(outflows),
        "net_position_gbp": float(net),
        "collected_all_time_gbp": float(collected_recent),
        "provisional": True,
        "plain_english": (
            "Conservative forecast from invoices due and recorded expenses — not bank balance."
            if net >= 0
            else "Forecast suggests cash pressure — review tax reserves and overdue invoices."
        ),
    }