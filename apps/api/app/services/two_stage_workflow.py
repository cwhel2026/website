from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.jobs import AppointmentStatus, AppointmentType, DryingStatus, Job, JobStatus


@dataclass
class SevenDayRisk:
    at_risk: bool
    days_remaining: int | None
    message: str


def compute_seven_day_target(
    preparation_completed_at: datetime, target_days: int = 7
) -> date:
    return (preparation_completed_at.astimezone(ZoneInfo("Europe/London")).date() + timedelta(days=target_days))


def assess_seven_day_risk(job: Job, today: date | None = None) -> SevenDayRisk:
    today = today or datetime.now(UTC).date()
    if job.seven_day_target_date is None:
        return SevenDayRisk(False, None, "No seven-day target set")
    if job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
        return SevenDayRisk(False, None, "Job finished")
    if job.coating_completed_at is not None:
        return SevenDayRisk(False, None, "Coating completed")

    remaining = (job.seven_day_target_date - today).days
    if remaining < 0:
        return SevenDayRisk(
            True,
            remaining,
            "Seven-day coating target exceeded — notify owner and customer",
        )
    if remaining <= 2:
        return SevenDayRisk(
            True,
            remaining,
            "Urgent: limited time remaining for safe coating window",
        )
    return SevenDayRisk(False, remaining, "Within seven-day target")


def sync_job_status_from_appointments(
    job: Job,
    *,
    customer_washed_already: bool = False,
) -> None:
    if job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.ON_HOLD):
        return
    active = [a for a in job.appointments if a.status != AppointmentStatus.CANCELLED]
    prep = [a for a in active if a.appointment_type == AppointmentType.PREPARATION]
    coat = [a for a in active if a.appointment_type == AppointmentType.COATING]
    if prep and all(a.completed_at for a in prep):
        if job.preparation_completed_at is None:
            job.preparation_completed_at = max(a.completed_at for a in prep)
            job.seven_day_target_date = compute_seven_day_target(job.preparation_completed_at)
            job.drying_status = DryingStatus.AWAITING_DRY
    ready = bool(job.preparation_completed_at or customer_washed_already or not job.requires_two_stage)
    if coat and ready and all(a.completed_at for a in coat):
        job.coating_completed_at = max(a.completed_at for a in coat)
        job.status = JobStatus.COMPLETED
    elif coat and ready:
        job.status = JobStatus.COATING_SCHEDULED
    elif job.preparation_completed_at or customer_washed_already:
        job.status = JobStatus.RESTORATION_PENDING
    elif prep:
        job.status = JobStatus.PREPARATION_SCHEDULED
    elif active:
        job.status = JobStatus.COMPLETED if not job.requires_two_stage and all(a.completed_at for a in active) else JobStatus.BOOKED
    else:
        job.status = JobStatus.AWAITING_PREP_BOOKING
