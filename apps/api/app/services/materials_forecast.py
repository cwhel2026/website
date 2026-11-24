from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import StockItem
from app.models.jobs import Appointment, AppointmentType, Job
from app.models.quotation import Quotation


@dataclass
class MaterialNeed:
    stock_sku: str
    stock_name: str
    quantity_needed: Decimal
    unit: str
    reason: str


async def forecast_coating_for_days(db: AsyncSession, days: int = 7) -> list[MaterialNeed]:
    start = datetime.now(UTC)
    end = start + timedelta(days=days)
    coating_item = await db.execute(
        select(StockItem).where(
            StockItem.is_active.is_(True),
            StockItem.sku == "COAT-TARMAC-20L",
        )
    )
    stock = coating_item.scalar_one_or_none()
    if stock is None or not stock.coverage_sqm_per_unit:
        return []

    coverage = stock.coverage_sqm_per_unit
    wastage = Decimal("1") + stock.wastage_allowance_pct / Decimal("100")

    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(
            Appointment.appointment_type == AppointmentType.COATING,
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start < end,
        )
    )
    total_sqm = Decimal("0")
    for _, job in result.all():
        if job.quotation_id:
            q = await db.get(Quotation, job.quotation_id)
            if q:
                total_sqm += q.total_area_sqm

    if total_sqm <= 0:
        return []

    litres = (total_sqm / coverage) * wastage
    needs = [
        MaterialNeed(
            stock_sku=stock.sku,
            stock_name=stock.name,
            quantity_needed=litres.quantize(Decimal("0.1")),
            unit=stock.unit,
            reason=f"Coating appointments in next {days} days ({total_sqm} sqm)",
        )
    ]
    return needs


async def low_stock_alerts(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(StockItem).where(StockItem.is_active.is_(True)))
    alerts = []
    for item in result.scalars().all():
        if item.quantity_on_hand <= item.reorder_level:
            alerts.append(
                {
                    "sku": item.sku,
                    "name": item.name,
                    "on_hand": float(item.quantity_on_hand),
                    "reorder_level": float(item.reorder_level),
                }
            )
    return alerts