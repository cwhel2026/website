from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models.crm import CustomerProperty
from app.models.jobs import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    DryingStatus,
    Job,
    JobStatus,
)
from app.models.quotation import Quotation
from app.models.service import Service
from app.models.user import User
from app.models.weather import ProductProfile
from app.schemas.jobs import (
    CompletePrepIn,
    CreateAppointmentIn,
    FieldJobOut,
    JobOut,
    ProposeScheduleOut,
    SlotProposalOut,
)
from app.services.scheduling_engine import (
    find_conflicts,
    get_scheduling_settings,
    job_from_quotation,
    propose_two_stage_slots,
)
from app.services.two_stage_workflow import assess_seven_day_risk, sync_job_status_from_appointments


router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_out(job: Job) -> JobOut:
    risk = assess_seven_day_risk(job)
    data = JobOut.model_validate(job)
    data.seven_day_at_risk = risk.at_risk
    data.seven_day_message = risk.message
    return data


@router.get("", response_model=list[JobOut])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[JobOut]:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).order_by(Job.created_at.desc()).limit(200)
    )
    return [_job_out(j) for j in result.scalars().all()]


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
    return [_job_out(j) for j in result.scalars().all()]


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
    _: Annotated[User, Depends(get_current_admin)],
) -> JobOut:
    q_result = await db.execute(select(Quotation).where(Quotation.id == quotation_id))
    quotation = q_result.scalar_one_or_none()
    if quotation is None:
        raise HTTPException(404, "Quotation not found")
    existing = await db.execute(select(Job).where(Job.quotation_id == quotation_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Job already exists for quotation")
    if quotation.service_id is None:
        raise HTTPException(400, "Quotation has no service")
    svc = await db.get(Service, quotation.service_id)
    if svc is None:
        raise HTTPException(400, "Service not found")
    job = await job_from_quotation(db, quotation, svc)
    await db.commit()
    await db.refresh(job, ["appointments"])
    return _job_out(job)


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
    return _job_out(job)


@router.get("/{job_id}/propose-schedule", response_model=ProposeScheduleOut)
async def propose_schedule(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    lat: float = 53.65,
    lon: float = -2.95,
) -> ProposeScheduleOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.customer_id:
        prop = await db.execute(
            select(CustomerProperty)
            .where(CustomerProperty.customer_id == job.customer_id)
            .order_by(CustomerProperty.id.desc())
            .limit(1)
        )
        property_row = prop.scalar_one_or_none()
        if property_row and property_row.latitude and property_row.longitude:
            lat = property_row.latitude
            lon = property_row.longitude
    pp = await db.execute(select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1))
    profile = pp.scalar_one_or_none()
    if profile is None:
        raise HTTPException(500, "No product profile configured")
    prep, coat = await propose_two_stage_slots(db, job=job, lat=lat, lon=lon, product_profile=profile)
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
    _: Annotated[User, Depends(get_current_admin)],
) -> JobOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
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
    conflicts = await find_conflicts(db, body.scheduled_start, end)
    if conflicts and not body.confirm:
        raise HTTPException(
            409,
            detail={"message": "Scheduling conflicts", "conflicts": [c.reason for c in conflicts]},
        )
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
    )
    db.add(appt)
    sync_job_status_from_appointments(job, customer_washed_already=job.customer_washed_already)
    if job.status == JobStatus.BOOKED and job.appointments:
        job.status = JobStatus.PREPARATION_SCHEDULED
    await db.commit()
    await db.refresh(job, ["appointments"])
    return _job_out(job)


@router.post("/{job_id}/complete-preparation", response_model=JobOut)
async def complete_preparation(
    job_id: UUID,
    body: CompletePrepIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> JobOut:
    result = await db.execute(
        select(Job).options(selectinload(Job.appointments)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Job not found")
    completed = body.completed_at or datetime.now(UTC)
    for appt in job.appointments:
        if appt.appointment_type == AppointmentType.PREPARATION:
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
    return _job_out(job)