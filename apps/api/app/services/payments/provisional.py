"""Reserve a provisional visit without confirming a booking or contacting customers."""
from datetime import UTC, datetime, timedelta
from sqlalchemy import select, text
from app.models.jobs import Job, JobStatus, Appointment, AppointmentStatus, AppointmentType
from app.models.crm import Customer, CustomerProperty


async def reserve_provisional_visit(db, job_id, start: datetime, end: datetime):
    if start.utcoffset() is None or end.utcoffset() is None:
        raise ValueError("Explicit timezone required")
    if start <= datetime.now(UTC) or not timedelta(minutes=15) <= end-start <= timedelta(hours=12):
        raise ValueError("Invalid future appointment duration")
    if (end-start).total_seconds() % 60:
        raise ValueError("Whole-minute duration required")
    # Serialize reservations through this service; other scheduling writers must share this lock.
    await db.execute(text("SELECT pg_advisory_xact_lock(731904221)"))
    job = await db.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if not job or job.status not in {JobStatus.DRAFT, JobStatus.AWAITING_PREP_BOOKING}:
        raise ValueError("Job is not eligible for provisional booking")
    customer = await db.get(Customer, job.customer_id)
    prop = await db.get(CustomerProperty, job.property_id) if job.property_id else None
    if not customer or customer.is_test or not prop or prop.customer_id != job.customer_id:
        raise ValueError("Verified customer property required")
    kind = AppointmentType.PREPARATION if job.requires_two_stage else AppointmentType.SINGLE_VISIT
    active = (AppointmentStatus.PROVISIONAL, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS)
    existing = await db.scalar(select(Appointment).where(
        Appointment.job_id == job.id, Appointment.appointment_type == kind,
        Appointment.status.in_(active)).limit(1))
    if existing:
        if existing.status == AppointmentStatus.PROVISIONAL and existing.scheduled_start == start and existing.scheduled_end == end:
            return existing
        raise ValueError("Existing visit must be reviewed before rescheduling")
    conflict = await db.scalar(select(Appointment.id).where(
        Appointment.status.in_(active), Appointment.scheduled_start < end,
        Appointment.scheduled_end > start).limit(1))
    if conflict:
        raise ValueError("Requested visit overlaps another reserved appointment")
    visit = Appointment(job_id=job.id, appointment_type=kind, status=AppointmentStatus.PROVISIONAL,
                        scheduled_start=start, scheduled_end=end,
                        duration_minutes=int((end-start).total_seconds()/60),
                        postcode=prop.postcode, latitude=prop.latitude, longitude=prop.longitude)
    db.add(visit)
    await db.flush()
    return visit
