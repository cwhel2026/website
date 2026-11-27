from datetime import UTC, date, datetime, timedelta

from app.models.jobs import Job, JobStatus
from app.services.two_stage_workflow import assess_seven_day_risk, compute_seven_day_target


def test_compute_seven_day_target():
    prep = datetime(2025, 6, 1, 14, 0, tzinfo=UTC)
    assert compute_seven_day_target(prep, 7) == date(2025, 6, 8)


def test_seven_day_risk_when_overdue():
    job = Job(
        reference="JOB-TEST",
        customer_id=__import__("uuid").uuid4(),
        status=JobStatus.RESTORATION_PENDING,
        seven_day_target_date=date.today() - timedelta(days=1),
    )
    risk = assess_seven_day_risk(job, today=date.today())
    assert risk.at_risk is True
    assert "exceeded" in risk.message


def test_seven_day_not_at_risk_when_future():
    job = Job(
        reference="JOB-TEST2",
        customer_id=__import__("uuid").uuid4(),
        status=JobStatus.RESTORATION_PENDING,
        seven_day_target_date=date.today() + timedelta(days=5),
    )
    risk = assess_seven_day_risk(job, today=date.today())
    assert risk.at_risk is False

def test_completed_coating_advances_job_and_preserves_dry_confirmation():
    from types import SimpleNamespace
    from app.models.jobs import AppointmentType, AppointmentStatus, DryingStatus
    from app.services.two_stage_workflow import sync_job_status_from_appointments

    now = datetime.now(UTC)
    job = SimpleNamespace(status=JobStatus.COATING_SCHEDULED, requires_two_stage=True,
                          preparation_completed_at=now-timedelta(days=1),
                          coating_completed_at=None, drying_status=DryingStatus.CONFIRMED_ON_SITE,
                          appointments=[SimpleNamespace(appointment_type=AppointmentType.COATING,
                              status=AppointmentStatus.COMPLETED, completed_at=now)])
    sync_job_status_from_appointments(job)
    assert job.status == JobStatus.COMPLETED
    assert job.coating_completed_at == now
    assert job.drying_status == DryingStatus.CONFIRMED_ON_SITE
    sync_job_status_from_appointments(job)
    assert job.status == JobStatus.COMPLETED


def test_seven_day_target_uses_london_calendar():
    assert compute_seven_day_target(datetime(2027, 6, 1, 23, 30, tzinfo=UTC)) == date(2027, 6, 9)


def test_payment_rejects_negative_and_fractional_penny():
    import pytest
    from pydantic import ValidationError
    from app.routers.finance import PaymentIn
    for amount in ("-1", "0", "1.001"):
        with pytest.raises(ValidationError):
            PaymentIn(amount_gbp=amount)
