from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, Invoice, InvoiceStatus
from app.models.jobs import Job, JobStatus
from app.models.quotation import Quotation
from app.models.territory import Territory


@dataclass
class JobProfitability:
    job_reference: str
    quoted_revenue_gbp: Decimal
    estimated_contribution_gbp: Decimal
    expenses_gbp: Decimal
    estimated_profit_gbp: Decimal
    invoiced_net_gbp: Decimal = Decimal('0')
    recorded_direct_cost_margin_gbp: Decimal | None = None


@dataclass
class TerritoryProfitability:
    territory_code: str
    territory_name: str
    quoted_revenue_gbp: Decimal
    expenses_gbp: Decimal
    estimated_profit_gbp: Decimal


async def job_profitability(db: AsyncSession, job_id: UUID) -> JobProfitability | None:
    job = await db.get(Job, job_id)
    if job is None:
        return None
    quote_revenue = Decimal("0")
    contribution = Decimal("0")
    if job.quotation_id:
        q = await db.get(Quotation, job.quotation_id)
        if q and not q.is_test:
            quote_revenue = q.total_inc_vat_gbp
            contribution = q.estimated_contribution_gbp
    exp_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount_gbp), 0)).where(Expense.job_id == job_id)
    )
    expenses = Decimal(str(exp_result.scalar() or 0))
    # Estimated contribution already includes estimated costs. Do not deduct actual costs again.
    profit = contribution
    invoiced = await db.scalar(select(func.sum(Invoice.subtotal_ex_vat_gbp)).where(Invoice.job_id == job_id, Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.VOID])))
    net = Decimal(str(invoiced)) if invoiced is not None else None
    return JobProfitability(
        job_reference=job.reference,
        quoted_revenue_gbp=quote_revenue,
        estimated_contribution_gbp=contribution,
        expenses_gbp=expenses,
        estimated_profit_gbp=profit,
        invoiced_net_gbp=net or Decimal('0'),
        recorded_direct_cost_margin_gbp=net - expenses if net is not None else None,
    )


async def territory_profitability(db: AsyncSession) -> list[TerritoryProfitability]:
    territories = (await db.execute(select(Territory).where(Territory.is_active.is_(True)))).scalars().all()
    out: list[TerritoryProfitability] = []
    for t in territories:
        quote_sum = await db.execute(
            select(func.coalesce(func.sum(Quotation.total_inc_vat_gbp), 0)).where(
                Quotation.territory_id == t.id,
                Quotation.is_test.is_(False),
                Quotation.id.in_(select(Job.quotation_id).where(Job.status == JobStatus.COMPLETED))
            )
        )
        exp_sum = await db.execute(
            select(func.coalesce(func.sum(Expense.amount_gbp), 0)).where(Expense.territory_id == t.id)
        )
        contrib = await db.execute(
            select(func.coalesce(func.sum(Quotation.estimated_contribution_gbp), 0)).where(
                Quotation.territory_id == t.id,
                Quotation.is_test.is_(False),
                Quotation.id.in_(select(Job.quotation_id).where(Job.status == JobStatus.COMPLETED))
            )
        )
        revenue = Decimal(str(quote_sum.scalar() or 0))
        expenses = Decimal(str(exp_sum.scalar() or 0))
        contribution = Decimal(str(contrib.scalar() or 0))
        out.append(
            TerritoryProfitability(
                territory_code=t.code,
                territory_name=t.name,
                quoted_revenue_gbp=revenue,
                expenses_gbp=expenses,
                estimated_profit_gbp=contribution,
            )
        )
    return out