from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.models.jobs import AppointmentType, DryingStatus, Job, JobStatus


@dataclass
class SevenDayRisk:
    at_risk: bool
    days_remaining: int | None
    message: str


def compute_seven_day_target(
    preparation_completed_at: datetime, target_days: int = 7
) -> date:
    return (preparation_completed_at.astimezone(UTC).date() + timedelta(days=target_days))


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
    if customer_washed_already:
        job.requires_two_stage = True
        job.drying_status = DryingStatus.SURFACE_DRY
        if job.status == JobStatus.DRAFT:
            job.status = JobStatus.RESTORATION_PENDING
        return

    prep = [a for a in job.appointments if a.appointment_type == AppointmentType.PREPARATION]
    coat = [a for a in job.appointments if a.appointment_type == AppointmentType.COATING]

    if prep and all(a.completed_at for a in prep):
        job.status = JobStatus.PREPARATION_COMPLETED
        job.preparation_completed_at = max(a.completed_at for a in prep if a.completed_at)
        if job.preparation_completed_at:
            job.seven_day_target_date = compute_seven_day_target(job.preparation_completed_at)
            job.drying_status = DryingStatus.AWAITING_DRY
            job.status = JobStatus.RESTORATION_PENDING
    elif prep:
        job.status = JobStatus.PREPARATION_SCHEDULED
    elif coat and not prep:
        job.status = JobStatus.COATING_SCHEDULED
    elif not job.appointments:
        job.status = JobStatus.AWAITING_PREP_BOOKING