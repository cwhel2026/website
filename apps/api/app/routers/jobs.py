from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.crm import CustomerProperty, Enquiry, PipelineStage
from app.models.jobs import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    DryingStatus,
    Job,
    JobStatus,
)
from app.models.quotation import Quotation, QuotationStatus
from app.models.service import Service
from app.models.user import User
from app.models.weather import ProductProfile, WorkActivity
from app.services.weather.service import get_hourly_forecast
from app.services.weather_engine import score_window
from app.schemas.jobs import (
    CompletePrepIn,
    CompleteCoatIn,
    CreateAppointmentIn,
    FieldJobOut,
    JobOut,
    ProposeScheduleOut,
    SlotProposalOut,
)
from app.services.scheduling_engine import (
    find_conflicts,
    earliest_search_from,
    slot_inside_working_hours,
    get_scheduling_settings,
    job_from_quotation,
    propose_two_stage_slots,
)
from app.services.quote_photos import photo_counts_for_quotations
from app.services.two_stage_workflow import assess_seven_day_risk, sync_job_status_from_appointments


router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_out(job: Job, photo_count: int = 0) -> JobOut:
    risk = assess_seven_day_risk(job)
    data = JobOut.model_validate(job)
    data.seven_day_at_risk = risk.at_risk
    data.seven_day_message = risk.message
    data.photo_count = photo_count
    return data


async def _jobs_out(db: AsyncSession, jobs: list[Job]) -> list[JobOut]:
    counts = await photo_counts_for_quotations(db, [job.quotation_id for job in jobs if job.quotation_id])
    return [_job_out(job, counts.get(job.quotation_id, 0) if job.quotation_id else 0) for job in jobs]


@router.get("", response_model=list[JobOut])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[JobOut]:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).order_by(Job.created_at.desc()).limit(200)
    )
    return await _jobs_out(db, list(result.scalars().all()))


@router.get("/wash-pending-coat", response_model=list[JobOut])
async def wash_pending_coat(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[JobOut]:
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.appointments))
        .where(
            Job.status.in_(
                [JobStatus.RESTORATION_PENDING, JobStatus.PREPARATION_COMPLETED]
            )
        )
        .order_by(Job.seven_day_target_date.asc().nulls_last())
    )
    return await _jobs_out(db, list(result.scalars().all()))


@router.get("/field/today", response_model=list[FieldJobOut])
async def field_jobs_today(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[FieldJobOut]:
    day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    result = await db.execute(
        select(Job, Appointment)
        .join(Appointment)
        .where(
            Appointment.scheduled_start >= day_start,
            Appointment.scheduled_start < day_end,
        )
        .order_by(Appointment.scheduled_start)
        .limit(20)
    )
    out: list[FieldJobOut] = []
    for job, appt in result.all():
        tasks = ["Verify access and water", "Review weather suitability"]
        if appt.appointment_type == AppointmentType.PREPARATION:
            tasks.extend(["Before photos", "Pressure wash", "Record measurements"])
        elif appt.appointment_type == AppointmentType.COATING:
            tasks.extend(["Confirm surface dry", "Before photos", "Apply coating", "After photos"])
        out.append(
            FieldJobOut(
                job_id=job.id,
                reference=job.reference,
                status=job.status,
                postcode=appt.postcode,
                next_appointment_type=appt.appointment_type,
                next_appointment_start=appt.scheduled_start,
                tasks=tasks,
            )
        )
    return out


@router.post("/from-quotation/{quotation_id}", response_model=JobOut)
async def create_job_from_quotation(
    quotation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> JobOut:
    q_result = await db.execute(select(Quotation).where(Quotation.id == quotation_id).with_for_update())
    quotation = q_result.scalar_one_or_none()
    if quotation is None:
        raise HTTPException(404, "Quotation not found")
    if quotation.status != QuotationStatus.ACCEPTED or quotation.is_test:
        raise HTTPException(409, "An accepted non-test quotation is required")
    existing = await db.execute(select(Job).options(selectinload(Job.appointments)).where(Job.quotation_id == quotation_id))
    existing_job = existing.scalar_one_or_none()
    if existing_job:
        return (await _jobs_out(db, [existing_job]))[0]
    if quotation.service_id is None:
        raise HTTPException(400, "Quotation has no service")
    svc = await db.get(Service, quotation.service_id)
    if svc is None:
        raise HTTPException(400, "Service not found")
    job = await job_from_quotation(db, quotation, svc)
    await db.commit()
    await db.refresh(job, ["appointments"])
    return (await _jobs_out(db, [job]))[0]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> JobOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    return (await _jobs_out(db, [job]))[0]


@router.get("/{job_id}/propose-schedule", response_model=ProposeScheduleOut)
async def propose_schedule(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    lat: float | None = None,
    lon: float | None = None,
) -> ProposeScheduleOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.property_id:
        prop = await db.execute(
            select(CustomerProperty)
            .where(CustomerProperty.id == job.property_id, CustomerProperty.customer_id == job.customer_id)
            .order_by(CustomerProperty.id.desc())
            .limit(1)
        )
        property_row = prop.scalar_one_or_none()
        if property_row and property_row.latitude is not None and property_row.longitude is not None:
            lat = property_row.latitude
            lon = property_row.longitude
    if lat is None or lon is None:
        raise HTTPException(422, "Property coordinates required for weather scheduling")
    pp = await db.execute(select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1))
    profile = pp.scalar_one_or_none()
    if profile is None:
        raise HTTPException(500, "No product profile configured")
    try:
        prep, coat = await propose_two_stage_slots(db, job=job, lat=lat, lon=lon, product_profile=profile)
    except RuntimeError as exc:
        raise HTTPException(503, "Live weather unavailable") from exc
    return ProposeScheduleOut(
        preparation_slots=[
            SlotProposalOut(
                start=s.start,
                end=s.end,
                appointment_type=s.appointment_type,
                travel_minutes=s.travel_minutes,
                weather_score=s.weather_score,
                weather_safe=s.weather_safe,
            )
            for s in prep
        ],
        coating_slots=[
            SlotProposalOut(
                start=s.start,
                end=s.end,
                appointment_type=s.appointment_type,
                travel_minutes=s.travel_minutes,
                weather_score=s.weather_score,
                weather_safe=s.weather_safe,
            )
            for s in coat
        ],
    )


@router.post("/{job_id}/appointments", response_model=JobOut)
async def add_appointment(
    job_id: UUID,
    body: CreateAppointmentIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> JobOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id).with_for_update()
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.ON_HOLD):
        raise HTTPException(409, "Job is not open for booking")
    # Serialize bookings against the single diary settings row.
    from app.models.scheduling import SchedulingSettings
    await db.execute(select(SchedulingSettings).with_for_update())
    settings = await get_scheduling_settings(db)
    duration = body.duration_minutes
    if duration is None:
        if body.appointment_type == AppointmentType.PREPARATION:
            duration = settings.default_prep_duration_minutes
        elif body.appointment_type == AppointmentType.COATING:
            duration = settings.default_coat_duration_minutes
        else:
            duration = 120
    end = body.scheduled_start + timedelta(minutes=duration)
    if body.scheduled_start.tzinfo is None or duration <= 0 or body.scheduled_start < earliest_search_from(settings) or not slot_inside_working_hours(settings, body.scheduled_start, end):
        raise HTTPException(422, "Appointment must be in a future working window")
    if body.appointment_type == AppointmentType.COATING and job.requires_two_stage and not job.customer_washed_already:
        prep_end = job.preparation_completed_at or max((a.scheduled_end for a in job.appointments if a.appointment_type == AppointmentType.PREPARATION and a.status == AppointmentStatus.CONFIRMED), default=None)
        if prep_end is None or body.scheduled_start < prep_end + timedelta(hours=settings.min_drying_hours):
            raise HTTPException(409, "Coating must follow preparation and drying")
    if any(a.appointment_type == body.appointment_type and a.status in (AppointmentStatus.PROVISIONAL, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS) for a in job.appointments):
        raise HTTPException(409, "Existing active appointment of this type; review before rebooking")
    conflicts = await find_conflicts(db, body.scheduled_start, end)
    if conflicts:
        raise HTTPException(
            409,
            detail={"message": "Scheduling conflicts", "conflicts": [c.reason for c in conflicts]},
        )
    weather_safe = None
    if body.appointment_type in (AppointmentType.PREPARATION, AppointmentType.COATING):
        prop = await db.get(CustomerProperty, job.property_id) if job.property_id else None
        if prop is None or prop.customer_id != job.customer_id or prop.latitude is None or prop.longitude is None:
            raise HTTPException(422, "Job property coordinates required")
        body.latitude, body.longitude, body.postcode = prop.latitude, prop.longitude, prop.postcode
        if body.confirm:
            profile = await db.scalar(select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1))
            if profile is None:
                raise HTTPException(503, "Product weather profile unavailable")
            try:
                forecast, _, live = await get_hourly_forecast(db, prop.latitude, prop.longitude, hours=168, for_booking=True)
            except RuntimeError as exc:
                raise HTTPException(503, "Live weather unavailable") from exc
            activity = WorkActivity.COATING if body.appointment_type == AppointmentType.COATING else WorkActivity.WASHING
            score = score_window(activity, profile, forecast, body.scheduled_start, duration / 60)
            weather_safe = live and score.is_safe
            if not weather_safe:
                raise HTTPException(409, "Safe live forecast required; use provisional booking instead")
    appt = Appointment(
        job_id=job.id,
        appointment_type=body.appointment_type,
        status=AppointmentStatus.CONFIRMED if body.confirm else AppointmentStatus.PROVISIONAL,
        scheduled_start=body.scheduled_start,
        scheduled_end=end,
        duration_minutes=duration,
        latitude=body.latitude,
        longitude=body.longitude,
        postcode=body.postcode,
        weather_suitable=weather_safe,
    )
    job.appointments.append(appt)
    sync_job_status_from_appointments(job, customer_washed_already=job.customer_washed_already)
    if body.confirm and job.quotation_id:
        quote = await db.get(Quotation, job.quotation_id)
        if quote and quote.enquiry_id:
            enquiry = await db.get(Enquiry, quote.enquiry_id)
            if enquiry and enquiry.stage in (PipelineStage.QUOTE_ACCEPTED, PipelineStage.BOOKING_PENDING):
                enquiry.stage = PipelineStage.BOOKED
    await db.commit()
    await db.refresh(job, ["appointments"])
    return (await _jobs_out(db, [job]))[0]


@router.post("/{job_id}/complete-preparation", response_model=JobOut)
async def complete_preparation(
    job_id: UUID,
    body: CompletePrepIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> JobOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id).with_for_update()
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.ON_HOLD):
        raise HTTPException(409, "Job is not open")
    if job.preparation_completed_at:
        return (await _jobs_out(db, [job]))[0]
    completed = body.completed_at or datetime.now(UTC)
    if completed.tzinfo is None or completed > datetime.now(UTC):
        raise HTTPException(422, "Invalid completion time")
    if not any(a.appointment_type == AppointmentType.PREPARATION and a.status in (AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS) for a in job.appointments):
        raise HTTPException(409, "No confirmed preparation appointment")
    for appt in job.appointments:
        if appt.appointment_type == AppointmentType.PREPARATION and appt.status in (AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS):
            appt.completed_at = completed
            appt.status = AppointmentStatus.COMPLETED
    job.preparation_completed_at = completed
    job.status = JobStatus.RESTORATION_PENDING
    job.drying_status = (
        DryingStatus.SURFACE_DRY if body.surface_dry_confirmed else DryingStatus.AWAITING_DRY
    )
    from app.services.two_stage_workflow import compute_seven_day_target

    settings = await get_scheduling_settings(db)
    job.seven_day_target_date = compute_seven_day_target(
        completed, settings.seven_day_coating_target_days
    )
    await db.commit()
    await db.refresh(job, ["appointments"])
    return (await _jobs_out(db, [job]))[0]

@router.post("/{job_id}/complete-coating", response_model=JobOut)
async def complete_coating(
    job_id: UUID,
    body: CompleteCoatIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> JobOut:
    job = (await db.execute(select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id).with_for_update())).scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.status == JobStatus.COMPLETED:
        return (await _jobs_out(db, [job]))[0]
    if job.status in (JobStatus.CANCELLED, JobStatus.ON_HOLD):
        raise HTTPException(409, "Job is not open")
    if job.requires_two_stage and not (job.preparation_completed_at or job.customer_washed_already):
        raise HTTPException(409, "Complete preparation first")
    if not body.surface_dry_confirmed or not body.weather_safe_confirmed:
        raise HTTPException(422, "Confirm dry surface and safe on-site weather")
    completed = body.completed_at or datetime.now(UTC)
    if completed.tzinfo is None or completed > datetime.now(UTC) or (job.preparation_completed_at and completed < job.preparation_completed_at):
        raise HTTPException(422, "Invalid completion time")
    appts = [a for a in job.appointments if a.appointment_type == AppointmentType.COATING and a.status in (AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS)]
    if not appts:
        raise HTTPException(409, "No confirmed coating appointment")
    for appt in appts:
        appt.completed_at = completed
        appt.status = AppointmentStatus.COMPLETED
    job.drying_status = DryingStatus.CONFIRMED_ON_SITE
    sync_job_status_from_appointments(job, customer_washed_already=job.customer_washed_already)
    if job.status == JobStatus.COMPLETED and job.quotation_id:
        quote = await db.get(Quotation, job.quotation_id)
        if quote and quote.enquiry_id:
            enquiry = await db.get(Enquiry, quote.enquiry_id)
            if enquiry:
                enquiry.stage = PipelineStage.JOB_COMPLETED
    await db.commit()
    return (await _jobs_out(db, [job]))[0]
