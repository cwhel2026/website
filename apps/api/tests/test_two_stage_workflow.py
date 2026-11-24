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