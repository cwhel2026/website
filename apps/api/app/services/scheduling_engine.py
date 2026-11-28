from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.jobs import Appointment, AppointmentStatus, AppointmentType, DryingStatus, Job, JobStatus
from app.models.scheduling import OwnerCalendarBlock, SchedulingSettings
from app.models.quotation import Quotation
from app.models.service import Service
from app.services.geo import estimate_drive_minutes, haversine_km
from app.services.weather.service import get_hourly_forecast
from app.services.weather_engine import WorkActivity, score_window

LONDON = ZoneInfo("Europe/London")


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


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def earliest_search_from(settings: SchedulingSettings, now: datetime | None = None) -> datetime:
    """First instant a visit may start: London clock, after notice, inside hours, on/after launch."""
    now_utc = _aware_utc(now or datetime.now(UTC))
    local = now_utc.astimezone(LONDON)
    notice = timedelta(hours=int(getattr(settings, "min_notice_hours", 24) or 24))
    cursor = (now_utc + notice).astimezone(LONDON)
    work_start = settings.work_day_start or time(8, 0)
    work_end = settings.work_day_end or time(17, 30)
    launch = settings.earliest_work_date or date.min
    for _ in range(60):
        if cursor.date() < launch:
            cursor = datetime.combine(launch, work_start, tzinfo=LONDON)
            continue
        if cursor.weekday() >= 5:
            cursor = datetime.combine(cursor.date() + timedelta(days=1), work_start, tzinfo=LONDON)
            continue
        local_clock = cursor.timetz().replace(tzinfo=None)
        if local_clock < work_start:
            cursor = datetime.combine(cursor.date(), work_start, tzinfo=LONDON)
            local_clock = work_start
        if local_clock >= work_end:
            cursor = datetime.combine(cursor.date() + timedelta(days=1), work_start, tzinfo=LONDON)
            continue
        if cursor <= now_utc.astimezone(LONDON):
            cursor += timedelta(minutes=15)
            continue
        return cursor.astimezone(UTC)
    return cursor.astimezone(UTC)


def slot_inside_working_hours(settings: SchedulingSettings, start: datetime, end: datetime) -> bool:
    local_start = _aware_utc(start).astimezone(LONDON)
    local_end = _aware_utc(end).astimezone(LONDON)
    work_start = settings.work_day_start or time(8, 0)
    work_end = settings.work_day_end or time(17, 30)
    launch = settings.earliest_work_date or date.min
    if end <= start:
        return False
    if local_start.date() < launch or local_end.date() < launch:
        return False
    if local_start.weekday() >= 5 or local_end.weekday() >= 5:
        return False
    if local_start.date() != local_end.date():
        return False
    start_clock = local_start.timetz().replace(tzinfo=None)
    end_clock = local_end.timetz().replace(tzinfo=None)
    return work_start <= start_clock and end_clock <= work_end


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
    settings = await get_scheduling_settings(db)
    now = datetime.now(UTC)
    search_from = _aware_utc(search_from) if search_from else earliest_search_from(settings, now)
    if search_from < earliest_search_from(settings, now):
        search_from = earliest_search_from(settings, now)

    distance = haversine_km(
        float(settings.base_latitude),
        float(settings.base_longitude),
        lat,
        lon,
    )
    travel = estimate_drive_minutes(distance) + settings.travel_buffer_minutes
    forecast, _source, _live = await get_hourly_forecast(db, lat, lon, hours=168, for_booking=True)
    if not _live:
        raise RuntimeError("Live forecast required for scheduling proposals")

    prep_slots: list[SlotProposal] = []
    coat_slots: list[SlotProposal] = []

    cursor = search_from
    horizon = min(search_from + timedelta(days=21), max((h.forecast_time for h in forecast), default=now) + timedelta(hours=1))
    already_prepared = bool(job and (job.preparation_completed_at or job.customer_washed_already))
    while not already_prepared and len(prep_slots) < max_prep_slots and cursor < horizon:
        start = cursor
        end = start + timedelta(minutes=settings.default_prep_duration_minutes)
        if start > now and slot_inside_working_hours(settings, start, end):
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
        cursor += timedelta(hours=1)

    if not prep_slots and not already_prepared:
        return prep_slots, coat_slots

    prep_end = (job.preparation_completed_at or search_from - timedelta(hours=settings.min_drying_hours)) if already_prepared else prep_slots[0].end
    earliest_coat_start = max(
        prep_end + timedelta(hours=settings.min_drying_hours),
        earliest_search_from(settings, now),
    )
    coat_cursor = earliest_coat_start
    coat_horizon = prep_end + timedelta(days=settings.seven_day_coating_target_days)
    if job and job.seven_day_target_date:
        coat_horizon = datetime.combine(job.seven_day_target_date + timedelta(days=1), time.min, tzinfo=LONDON).astimezone(UTC)
    if already_prepared and coat_horizon <= earliest_coat_start:
        # Overdue jobs still need a safe recovery window.
        coat_horizon = earliest_coat_start + timedelta(days=7)
    while len(coat_slots) < max_prep_slots and coat_cursor < coat_horizon:
        c_start = coat_cursor
        c_end = c_start + timedelta(minutes=settings.default_coat_duration_minutes)
        if c_start > now and c_end <= coat_horizon and slot_inside_working_hours(settings, c_start, c_end):
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
        coat_cursor += timedelta(hours=1)

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
        property_id=quotation.property_id,
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