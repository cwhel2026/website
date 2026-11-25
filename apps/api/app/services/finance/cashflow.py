from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import cast, func, select
from sqlalchemy import Date as SaDate
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, ExpenseCategory, Invoice, InvoiceStatus, Payment
from app.models.jobs import Appointment, AppointmentStatus, Job, JobStatus
from app.models.quotation import Quotation
from app.services.finance.tax_reserves import compute_tax_reserves


async def _invoice_inflows(db: AsyncSession, horizon: date, *, factor: Decimal) -> Decimal:
    inv = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE]),
            Invoice.due_date <= horizon,
        )
    )
    total = Decimal("0")
    for row in inv.scalars().all():
        outstanding = row.total_inc_vat_gbp - row.amount_paid_gbp
        total += outstanding * factor
    return total


async def _confirmed_job_inflows(db: AsyncSession, today: date, horizon: date, *, factor: Decimal) -> Decimal:
    result = await db.execute(
        select(Job, Quotation)
        .join(Quotation, Job.quotation_id == Quotation.id, isouter=True)
        .where(
            Job.status.in_(
                [
                    JobStatus.BOOKED,
                    JobStatus.PREPARATION_SCHEDULED,
                    JobStatus.COATING_SCHEDULED,
                    JobStatus.RESTORATION_PENDING,
                ]
            )
        )
    )
    total = Decimal("0")
    for job, quote in result.all():
        target = job.seven_day_target_date or today
        if target > horizon:
            continue
        if quote and quote.total_inc_vat_gbp:
            unpaid = quote.total_inc_vat_gbp
            inv = await db.execute(select(Invoice).where(Invoice.job_id == job.id))
            for invoice in inv.scalars().all():
                unpaid = max(Decimal("0"), unpaid - invoice.amount_paid_gbp)
            total += unpaid * factor
    return total


async def _operating_outflows(db: AsyncSession, horizon: date, *, factor: Decimal) -> Decimal:
    exp = await db.execute(select(Expense).where(Expense.expense_date <= horizon))
    rows = list(exp.scalars().all())
    base = sum((e.amount_gbp for e in rows), Decimal("0"))
    marketing = sum((e.amount_gbp for e in rows if e.category == ExpenseCategory.ADVERTISING), Decimal("0"))
    return (base + marketing) * factor


async def _weather_drag_factor(db: AsyncSession, horizon: date) -> Decimal:
    """Reduce optimistic inflows when confirmed appointments are weather-delayed."""
    result = await db.execute(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.status == AppointmentStatus.WEATHER_DELAYED,
            cast(Appointment.scheduled_start, SaDate) <= horizon,
        )
    )
    delayed = int(result.scalar() or 0)
    if delayed == 0:
        return Decimal("1")
    return max(Decimal("0.7"), Decimal("1") - Decimal("0.05") * delayed)


async def _scenario_pack(
    db: AsyncSession,
    days: int,
    *,
    inflow_factor: Decimal,
    outflow_factor: Decimal,
    label: str,
) -> dict:
    today = date.today()
    horizon = today + timedelta(days=days)
    weather = await _weather_drag_factor(db, horizon)
    inflows = (
        await _invoice_inflows(db, horizon, factor=inflow_factor * weather)
        + await _confirmed_job_inflows(db, today, horizon, factor=inflow_factor * weather)
    )
    outflows = await _operating_outflows(db, horizon, factor=outflow_factor)
    reserves = await compute_tax_reserves(db)
    tax = Decimal(str(reserves.get("recommended_reserve_gbp", 0))) * Decimal("0.08")
    net = inflows - outflows - tax
    return {
        "scenario": label,
        "horizon_days": days,
        "expected_inflows_gbp": float(inflows),
        "known_outflows_gbp": float(outflows),
        "tax_reserve_slice_gbp": float(tax),
        "net_position_gbp": float(net),
        "weather_factor": float(weather),
        "provisional": True,
    }


async def simple_cashflow_forecast(db: AsyncSession, *, days: int = 30) -> dict:
    expected = await _scenario_pack(db, days, inflow_factor=Decimal("1"), outflow_factor=Decimal("1"), label="expected")
    net = Decimal(str(expected["net_position_gbp"]))
    return {
        "horizon_days": days,
        "expected_inflows_gbp": expected["expected_inflows_gbp"],
        "known_outflows_gbp": expected["known_outflows_gbp"],
        "net_position_gbp": float(net),
        "provisional": True,
        "plain_english": (
            "Conservative forecast from invoices due and recorded expenses — not bank balance."
            if net >= 0
            else "Forecast suggests cash pressure — review tax reserves and overdue invoices."
        ),
    }


async def multi_horizon_cashflow(db: AsyncSession) -> dict:
    horizons = (7, 30, 90, 365)
    out: dict = {"horizons": {}, "generated_for": date.today().isoformat(), "provisional": True}
    for days in horizons:
        conservative = await _scenario_pack(
            db, days, inflow_factor=Decimal("0.75"), outflow_factor=Decimal("1.15"), label="conservative"
        )
        expected = await _scenario_pack(
            db, days, inflow_factor=Decimal("1"), outflow_factor=Decimal("1"), label="expected"
        )
        optimistic = await _scenario_pack(
            db, days, inflow_factor=Decimal("1.2"), outflow_factor=Decimal("0.9"), label="optimistic"
        )
        out["horizons"][str(days)] = {
            "conservative": conservative,
            "expected": expected,
            "optimistic": optimistic,
        }
    exp = expected
    out["plain_english"] = (
        f"30-day expected net £{out['horizons']['30']['expected']['net_position_gbp']:.0f} "
        f"(conservative £{out['horizons']['30']['conservative']['net_position_gbp']:.0f})."
    )
    return out