from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.jobs import Appointment, AppointmentStatus, AppointmentType, DryingStatus, Job
from app.models.scheduling import OwnerCalendarBlock, SchedulingSettings
from app.models.quotation import Quotation
from app.models.service import Service
from app.services.geo import estimate_drive_minutes, haversine_km
from app.services.weather.service import get_hourly_forecast
from app.services.weather_engine import WorkActivity, score_window


@dataclass
class SlotProposal:
    start: datetime
    end: datetime
    appointment_type: AppointmentType
    travel_minutes: int
    weather_score: int | None
    weather_safe: bool | None


@dataclass
class SchedulingConflict:
    reason: str
    appointment_id: UUID | None = None


async def get_scheduling_settings(db: AsyncSession) -> SchedulingSettings:
    result = await db.execute(select(SchedulingSettings).limit(1))
    settings = result.scalar_one_or_none()
    if settings is None:
        raise ValueError("Scheduling settings not configured")
    return settings


async def find_conflicts(
    db: AsyncSession, start: datetime, end: datetime, exclude_appointment_id: UUID | None = None
) -> list[SchedulingConflict]:
    conflicts: list[SchedulingConflict] = []
    q = select(Appointment).where(
        Appointment.status.in_(
            [AppointmentStatus.PROVISIONAL, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS]
        ),
        Appointment.scheduled_start < end,
        Appointment.scheduled_end > start,
    )
    if exclude_appointment_id:
        q = q.where(Appointment.id != exclude_appointment_id)
    result = await db.execute(q)
    for appt in result.scalars().all():
        conflicts.append(SchedulingConflict("double_booking", appt.id))

    block_q = select(OwnerCalendarBlock).where(
        OwnerCalendarBlock.is_unavailable.is_(True),
        OwnerCalendarBlock.block_start < end,
        OwnerCalendarBlock.block_end > start,
    )
    blocks = await db.execute(block_q)
    for block in blocks.scalars().all():
        conflicts.append(SchedulingConflict(f"owner_unavailable:{block.title}"))
    return conflicts


async def propose_two_stage_slots(
    db: AsyncSession,
    *,
    job: Job | None = None,
    lat: float,
    lon: float,
    product_profile,
    search_from: datetime | None = None,
    max_prep_slots: int = 5,
) -> tuple[list[SlotProposal], list[SlotProposal]]:
    """Find open preparation and coating windows. Does not create a job or appointment.

    ``job`` is accepted for existing callers and is not written.
    """
    del job
    settings = await get_scheduling_settings(db)
    search_from = search_from or datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)

    distance = haversine_km(
        float(settings.base_latitude),
        float(settings.base_longitude),
        lat,
        lon,
    )
    travel = estimate_drive_minutes(distance) + settings.travel_buffer_minutes
    forecast, _source, _live = await get_hourly_forecast(db, lat, lon, hours=72, for_booking=True)

    prep_slots: list[SlotProposal] = []
    coat_slots: list[SlotProposal] = []

    cursor = search_from
    while len(prep_slots) < max_prep_slots and cursor < search_from + timedelta(days=14):
        start = cursor
        end = start + timedelta(minutes=settings.default_prep_duration_minutes)
        conflicts = await find_conflicts(db, start, end)
        wash_score = score_window(
            WorkActivity.WASHING,
            product_profile,
            forecast,
            start,
            settings.default_prep_duration_minutes / 60,
        )
        if not conflicts and wash_score.is_safe:
            prep_slots.append(
                SlotProposal(
                    start=start,
                    end=end,
                    appointment_type=AppointmentType.PREPARATION,
                    travel_minutes=travel,
                    weather_score=wash_score.score,
                    weather_safe=wash_score.is_safe,
                )
            )
        cursor += timedelta(hours=3)

    if not prep_slots:
        return prep_slots, coat_slots

    earliest_coat_start = prep_slots[0].end + timedelta(hours=settings.min_drying_hours)
    coat_cursor = earliest_coat_start
    while len(coat_slots) < max_prep_slots and coat_cursor < prep_slots[0].start + timedelta(days=settings.seven_day_coating_target_days):
        c_start = coat_cursor
        c_end = c_start + timedelta(minutes=settings.default_coat_duration_minutes)
        conflicts = await find_conflicts(db, c_start, c_end)
        coat_score = score_window(
            WorkActivity.COATING,
            product_profile,
            forecast,
            c_start,
            settings.default_coat_duration_minutes / 60,
        )
        if not conflicts and coat_score.is_safe and coat_score.score >= 65:
            coat_slots.append(
                SlotProposal(
                    start=c_start,
                    end=c_end,
                    appointment_type=AppointmentType.COATING,
                    travel_minutes=travel,
                    weather_score=coat_score.score,
                    weather_safe=coat_score.is_safe,
                )
            )
        coat_cursor += timedelta(hours=4)

    return prep_slots, coat_slots


async def load_job(db: AsyncSession, job_id: UUID) -> Job | None:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id)
    )
    return result.scalar_one_or_none()


async def job_from_quotation(
    db: AsyncSession, quotation: Quotation, service: Service
) -> Job:
    requires_two = service.requires_washing and service.requires_coating
    job = Job(
        reference=f"JOB-{quotation.reference}",
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        territory_id=quotation.territory_id,
        requires_two_stage=requires_two,
        customer_washed_already=quotation.customer_washed_already,
        status=JobStatus.AWAITING_PREP_BOOKING if requires_two else JobStatus.BOOKED,
    )
    if quotation.customer_washed_already and service.requires_coating:
        job.status = JobStatus.RESTORATION_PENDING
        job.drying_status = DryingStatus.SURFACE_DRY
    db.add(job)
    await db.flush()
    return job