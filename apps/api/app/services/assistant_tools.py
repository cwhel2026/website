from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.approvals import ApprovalRequest, ApprovalStatus
from app.models.jobs import Appointment, AppointmentType, Job, JobStatus
from app.models.quotation import Quotation


async def tool_jobs_tomorrow(db: AsyncSession) -> dict[str, Any]:
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    start = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=UTC)
    end = start + timedelta(days=1)
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(Appointment.scheduled_start >= start, Appointment.scheduled_start < end)
        .order_by(Appointment.scheduled_start)
    )
    items = []
    for appt, job in result.all():
        items.append(
            {
                "job_reference": job.reference,
                "type": appt.appointment_type.value,
                "start": appt.scheduled_start.isoformat(),
                "postcode": appt.postcode,
            }
        )
    return {"date": tomorrow.isoformat(), "appointments": items, "count": len(items)}


async def tool_jobs_next_week(db: AsyncSession) -> dict[str, Any]:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(Appointment.scheduled_start >= start, Appointment.scheduled_start < end)
        .order_by(Appointment.scheduled_start)
    )
    by_day: dict[str, int] = {}
    for appt, _ in result.all():
        day = appt.scheduled_start.date().isoformat()
        by_day[day] = by_day.get(day, 0) + 1
    return {"days": by_day, "total": sum(by_day.values())}


async def tool_wash_pending_coat(db: AsyncSession) -> dict[str, Any]:
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.appointments))
        .where(Job.status.in_([JobStatus.RESTORATION_PENDING, JobStatus.PREPARATION_COMPLETED]))
        .order_by(Job.seven_day_target_date.asc().nulls_last())
        .limit(20)
    )
    jobs = []
    for j in result.scalars().all():
        jobs.append(
            {
                "reference": j.reference,
                "target_date": j.seven_day_target_date.isoformat() if j.seven_day_target_date else None,
            }
        )
    return {"count": len(jobs), "jobs": jobs}


async def tool_pending_approvals(db: AsyncSession) -> dict[str, Any]:
    result = await db.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.status == ApprovalStatus.PENDING)
        .order_by(ApprovalRequest.created_at.desc())
        .limit(20)
    )
    items = [
        {"id": str(a.id), "type": a.approval_type.value, "title": a.title}
        for a in result.scalars().all()
    ]
    return {"count": len(items), "approvals": items}


async def tool_quotations_awaiting(db: AsyncSession) -> dict[str, Any]:
    result = await db.execute(
        select(Quotation)
        .where(Quotation.requires_approval.is_(True))
        .order_by(Quotation.created_at.desc())
        .limit(20)
    )
    return {
        "quotations": [
            {"reference": q.reference, "total_inc_vat": float(q.total_inc_vat_gbp)}
            for q in result.scalars().all()
        ]
    }


async def tool_rain_risk_appointments(db: AsyncSession) -> dict[str, Any]:
    start = datetime.now(UTC)
    end = start + timedelta(days=3)
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start < end,
            Appointment.appointment_type == AppointmentType.COATING,
        )
    )
    at_risk = []
    for appt, job in result.all():
        if appt.weather_suitable is False:
            at_risk.append(
                {"job": job.reference, "start": appt.scheduled_start.isoformat()}
            )
    return {"count": len(at_risk), "appointments": at_risk}


async def tool_new_enquiries_count(db: AsyncSession) -> dict[str, Any]:
    from app.models.crm import Enquiry, PipelineStage

    since = datetime.now(UTC) - timedelta(days=7)
    result = await db.execute(
        select(func.count())
        .select_from(Enquiry)
        .where(Enquiry.created_at >= since, Enquiry.stage == PipelineStage.NEW_ENQUIRY)
    )
    count = result.scalar() or 0
    return {"last_7_days_new_enquiries": count}


TOOL_HANDLERS = {
    "jobs_tomorrow": tool_jobs_tomorrow,
    "jobs_next_week": tool_jobs_next_week,
    "wash_pending_coat": tool_wash_pending_coat,
    "pending_approvals": tool_pending_approvals,
    "quotations_awaiting": tool_quotations_awaiting,
    "rain_risk_coating": tool_rain_risk_appointments,
    "new_enquiries": tool_new_enquiries_count,
}