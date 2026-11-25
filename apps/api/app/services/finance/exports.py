import csv
import io
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, Invoice


async def export_invoices_csv(db: AsyncSession) -> str:
    result = await db.execute(select(Invoice).order_by(Invoice.issue_date))
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["invoice_number", "status", "issue_date", "due_date", "total_inc_vat", "amount_paid", "freeagent_id"]
    )
    for inv in result.scalars().all():
        writer.writerow(
            [
                inv.invoice_number,
                inv.status.value,
                inv.issue_date.isoformat(),
                inv.due_date.isoformat(),
                float(inv.total_inc_vat_gbp),
                float(inv.amount_paid_gbp),
                inv.freeagent_id or "",
            ]
        )
    return buf.getvalue()


async def export_expenses_csv(db: AsyncSession) -> str:
    result = await db.execute(select(Expense).order_by(Expense.expense_date.desc()))
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["expense_date", "description", "category", "amount_gbp", "vat_gbp", "source"])
    for exp in result.scalars().all():
        writer.writerow(
            [
                exp.expense_date.isoformat(),
                exp.description,
                exp.category.value,
                float(exp.amount_gbp),
                float(exp.vat_gbp),
                exp.source.value,
            ]
        )
    return buf.getvalue()


def year_end_pack_metadata() -> dict:
    return {
        "generated_on": date.today().isoformat(),
        "contents": [
            "Invoice CSV export",
            "Expense CSV export",
            "Bookkeeping review queue snapshot",
            "Tax reserve snapshot",
            "Compliance obligations list",
        ],
        "note": "Hand to accountant with FreeAgent access — not a statutory filing pack.",
    }