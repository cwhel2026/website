"""Capacity-aware marketing calculations — one owner / one van; global diary is authoritative."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import CustomerProperty, Enquiry
from app.models.jobs import Appointment, Job
from app.models.quotation import Quotation
from app.models.territory import Territory

# Operational defaults for a solo owner + one van (configurable later via settings table)
HORIZON_DAYS = 14
MAX_APPOINTMENTS_PER_DAY = 2
UTILISATION_FACTOR = Decimal("0.85")
GLOBAL_DAILY_AD_CAP_GBP = Decimal("35")
GLOBAL_MONTHLY_AD_CAP_GBP = Decimal("450")


@dataclass
class GlobalCapacitySnapshot:
    horizon_days: int
    max_slots: int
    booked_slots: int
    spare_slots: int
    spare_score: int
    max_appointments_per_day: int
    recommend_advertising: bool
    advertising_daily_budget_cap_gbp: Decimal
    note: str


@dataclass
class TerritoryDemandInsight:
    territory_id: str
    territory_code: str
    territory_name: str
    appointments_next_14_days: int
    enquiries_next_14_days: int
    quotations_next_14_days: int
    demand_score: int
    allocated_spare_slots: int
    recommend_advertising: bool
    recommendation: str
    suggested_daily_budget_gbp: Decimal


async def global_capacity_snapshot(db: AsyncSession) -> GlobalCapacitySnapshot:
    now = datetime.now(UTC)
    window_end = now + timedelta(days=HORIZON_DAYS)
    booked = await db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.scheduled_start >= now, Appointment.scheduled_start < window_end)
    )
    booked_slots = int(booked or 0)
    max_slots = int(
        HORIZON_DAYS * MAX_APPOINTMENTS_PER_DAY * float(UTILISATION_FACTOR)
    )
    spare = max(0, max_slots - booked_slots)
    spare_score = int((spare / max_slots) * 100) if max_slots else 0
    recommend = spare >= 4
    if booked_slots >= max_slots:
        note = "Diary at or above practical capacity — do not increase paid demand."
        recommend = False
    elif spare >= 8:
        note = "Healthy spare capacity — selective regional tests are appropriate."
    elif spare >= 3:
        note = "Limited spare capacity — small experiments only."
    else:
        note = "Very low spare capacity — pause prospecting ads."
        recommend = False

    daily_cap = GLOBAL_DAILY_AD_CAP_GBP if recommend else Decimal("0")
    return GlobalCapacitySnapshot(
        horizon_days=HORIZON_DAYS,
        max_slots=max_slots,
        booked_slots=booked_slots,
        spare_slots=spare,
        spare_score=spare_score,
        max_appointments_per_day=MAX_APPOINTMENTS_PER_DAY,
        recommend_advertising=recommend,
        advertising_daily_budget_cap_gbp=daily_cap,
        note=note,
    )


async def territory_demand_insights(db: AsyncSession) -> tuple[GlobalCapacitySnapshot, list[TerritoryDemandInsight]]:
    global_cap = await global_capacity_snapshot(db)
    now = datetime.now(UTC)
    window_end = now + timedelta(days=HORIZON_DAYS)

    territories = (await db.execute(select(Territory).where(Territory.is_active.is_(True)))).scalars().all()
    raw: list[TerritoryDemandInsight] = []

    for t in territories:
        appt_count = await db.scalar(
            select(func.count())
            .select_from(Appointment)
            .join(Job)
            .where(
                Job.territory_id == t.id,
                Appointment.scheduled_start >= now,
                Appointment.scheduled_start < window_end,
            )
        )
        enq_count = await db.scalar(
            select(func.count())
            .select_from(Enquiry)
            .join(CustomerProperty, CustomerProperty.customer_id == Enquiry.customer_id)
            .where(
                CustomerProperty.territory_id == t.id,
                Enquiry.created_at >= now - timedelta(days=HORIZON_DAYS),
            )
        )
        quote_count = await db.scalar(
            select(func.count())
            .select_from(Quotation)
            .where(Quotation.territory_id == t.id, Quotation.created_at >= now - timedelta(days=HORIZON_DAYS))
        )
        appts = int(appt_count or 0)
        enqs = int(enq_count or 0)
        quotes = int(quote_count or 0)
        demand_score = quotes * 3 + enqs
        raw.append(
            TerritoryDemandInsight(
                territory_id=str(t.id),
                territory_code=t.code,
                territory_name=t.name,
                appointments_next_14_days=appts,
                enquiries_next_14_days=enqs,
                quotations_next_14_days=quotes,
                demand_score=demand_score,
                allocated_spare_slots=0,
                recommend_advertising=False,
                recommendation="Hold — capacity allocated elsewhere.",
                suggested_daily_budget_gbp=Decimal("0"),
            )
        )

    if global_cap.spare_slots <= 0 or not raw:
        return global_cap, raw

    ranked = sorted(raw, key=lambda x: (x.demand_score, -x.appointments_next_14_days), reverse=True)
    spare_left = global_cap.spare_slots
    budget_pool = float(global_cap.advertising_daily_budget_cap_gbp)
    n = min(len(ranked), 3)

    for i, insight in enumerate(ranked[:n]):
        if spare_left < 2:
            break
        alloc = min(3, spare_left)
        spare_left -= alloc
        insight.allocated_spare_slots = alloc
        insight.recommend_advertising = global_cap.recommend_advertising and insight.demand_score >= 0
        share = budget_pool / n if n else 0
        insight.suggested_daily_budget_gbp = Decimal(str(round(share, 2)))
        if insight.recommend_advertising:
            insight.recommendation = (
                f"Test budget up to £{insight.suggested_daily_budget_gbp}/day — "
                f"{alloc} spare slot(s) allocated from global capacity."
            )
        else:
            insight.recommendation = "Monitor only — insufficient demand signal."

    for insight in ranked[n:]:
        insight.recommendation = "Not prioritised this cycle — global capacity reserved for higher-demand areas."

    return global_cap, sorted(ranked, key=lambda x: x.territory_code)