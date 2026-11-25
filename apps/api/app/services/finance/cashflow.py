"""Dated cash-flow projections — forecasts only, never bank authority."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import cast, func, select
from sqlalchemy import Date as SaDate
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BankTransaction, Invoice, InvoiceStatus
from app.models.jobs import Appointment, AppointmentStatus, Job, JobStatus
from app.services.compliance.engine import upcoming_reminders
from app.services.finance.tax_reserves import compute_tax_reserves


async def _opening_cash_gbp(db: AsyncSession) -> dict:
    result = await db.execute(select(BankTransaction))
    total = sum((t.amount_gbp for t in result.scalars().all()), Decimal("0"))
    if total == 0:
        return {"status": "unknown", "amount_gbp": None}
    return {"status": "estimated", "amount_gbp": float(total), "note": "Sum of synced bank lines — reconcile to actual balance."}


async def _invoice_inflows(db: AsyncSession, today: date, horizon: date, *, factor: Decimal) -> Decimal:
    inv = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE]),
            Invoice.due_date >= today,
            Invoice.due_date <= horizon,
        )
    )
    total = Decimal("0")
    for row in inv.scalars().all():
        total += (row.total_inc_vat_gbp - row.amount_paid_gbp) * factor
    return total


async def _job_inflows_without_invoice(db: AsyncSession, today: date, horizon: date, *, factor: Decimal) -> Decimal:
    """Jobs with no invoice yet — avoid double count with invoice table."""
    booked = await db.execute(
        select(Job).where(
            Job.status.in_(
                [JobStatus.BOOKED, JobStatus.PREPARATION_SCHEDULED, JobStatus.COATING_SCHEDULED, JobStatus.RESTORATION_PENDING]
            )
        )
    )
    total = Decimal("0")
    for job in booked.scalars().all():
        target = job.seven_day_target_date or today
        if target < today or target > horizon:
            continue
        inv = await db.execute(select(Invoice).where(Invoice.job_id == job.id))
        if inv.scalar_one_or_none():
            continue
        total += Decimal("0")
    return total * factor


async def _statutory_outflows(db: AsyncSession, today: date, horizon: date) -> Decimal:
    obligations = await upcoming_reminders(db, within_days=(horizon - today).days)
    total = Decimal("0")
    for ob in obligations:
        due = ob.get("due_date")
        if not due:
            continue
        d = date.fromisoformat(due)
        if today <= d <= horizon:
            total += Decimal("0")
    return total


async def _weather_factor(db: AsyncSession, horizon: date) -> Decimal:
    delayed = await db.execute(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.status == AppointmentStatus.WEATHER_DELAYED,
            cast(Appointment.scheduled_start, SaDate) <= horizon,
        )
    )
    n = int(delayed.scalar() or 0)
    if n == 0:
        return Decimal("1")
    return max(Decimal("0.75"), Decimal("1") - Decimal("0.03") * n)


async def _horizon_projection(
    db: AsyncSession,
    days: int,
    *,
    inflow_factor: Decimal,
    outflow_factor: Decimal,
    label: str,
) -> dict:
    today = date.today()
    horizon = today + timedelta(days=days)
    opening = await _opening_cash_gbp(db)
    reserves = await compute_tax_reserves(db)
    obligation_reserve = Decimal(str(reserves["recommended_reserve_gbp"] or 0))

    weather = await _weather_factor(db, horizon)
    inflows = (
        await _invoice_inflows(db, today, horizon, factor=inflow_factor * weather)
        + await _job_inflows_without_invoice(db, today, horizon, factor=inflow_factor * weather)
    )
    statutory = await _statutory_outflows(db, today, horizon)
    outflows = statutory * outflow_factor

    opening_amt = Decimal(str(opening["amount_gbp"] or 0))
    closing = opening_amt + inflows - outflows
    after_reserves = closing - obligation_reserve

    return {
        "scenario": label,
        "horizon_days": days,
        "assumptions": {
            "inflow_factor": float(inflow_factor),
            "outflow_factor": float(outflow_factor),
            "weather_factor": float(weather),
        },
        "opening_cash_gbp": opening,
        "inflows_gbp": float(inflows),
        "outflows_gbp": float(outflows),
        "closing_cash_gbp": float(closing),
        "tax_reserve_obligation_gbp": float(obligation_reserve),
        "available_after_reserves_gbp": float(after_reserves),
        "is_forecast": True,
        "provisional": reserves.get("is_provisional", True),
    }


async def simple_cashflow_forecast(db: AsyncSession, *, days: int = 30) -> dict:
    expected = await _horizon_projection(db, days, inflow_factor=Decimal("1"), outflow_factor=Decimal("1"), label="expected")
    closing = expected["closing_cash_gbp"]
    return {
        "horizon_days": days,
        "opening_cash_gbp": expected["opening_cash_gbp"],
        "expected_inflows_gbp": expected["inflows_gbp"],
        "known_outflows_gbp": expected["outflows_gbp"],
        "closing_cash_gbp": closing,
        "available_after_reserves_gbp": expected["available_after_reserves_gbp"],
        "is_forecast": True,
        "provisional": expected["provisional"],
        "plain_english": "Forecast only — verify opening cash against bank and FreeAgent.",
    }


async def multi_horizon_cashflow(db: AsyncSession) -> dict:
    horizons = (7, 30, 90, 365)
    out: dict = {"horizons": {}, "generated_for": date.today().isoformat(), "is_forecast": True}
    for days in horizons:
        out["horizons"][str(days)] = {
            "conservative": await _horizon_projection(db, days, inflow_factor=Decimal("0.8"), outflow_factor=Decimal("1"), label="conservative"),
            "expected": await _horizon_projection(db, days, inflow_factor=Decimal("1"), outflow_factor=Decimal("1"), label="expected"),
            "optimistic": await _horizon_projection(db, days, inflow_factor=Decimal("1.1"), outflow_factor=Decimal("0.95"), label="optimistic"),
        }
    out["plain_english"] = (
        f"30-day expected closing cash £{out['horizons']['30']['expected']['closing_cash_gbp']:.0f} "
        f"(after reserves £{out['horizons']['30']['expected']['available_after_reserves_gbp']:.0f})."
    )
    return out