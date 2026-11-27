from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.approvals import ApprovalRequest, ApprovalStatus
from app.models.jobs import Appointment, AppointmentStatus, AppointmentType, Job, JobStatus
from app.models.quotation import Quotation
from app.services.analytics_service import build_analytics_snapshot
from app.services.marketing.budget_controls import weekly_spend_summary
from app.services.marketing.capacity_engine import global_capacity_snapshot, territory_demand_insights
from app.services.marketing.director import build_daily_marketing_plan
from app.services.marketing.budget_controls import emergency_pause_connected_platforms, get_or_create_budget_policy
from app.services.marketing.director_proactive import run_daily_director_cycle
from app.services.marketing.integration_setup import build_integration_centre
from app.services.marketing.launch_readiness import assess_launch_readiness
from app.services.marketing.prospect_categories import PROSPECT_VERTICALS, vertical_places_queries
from app.services.marketing.content_calendar import calendar_view
from app.services.marketing.marketing_profitability import marketing_profitability_snapshot
from app.services.uk_time import uk_date_label, uk_now, uk_today, utc_range_for_uk_day


async def _appointments_between(db: AsyncSession, start: datetime, end: datetime) -> list[dict]:
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(Appointment.scheduled_start >= start, Appointment.scheduled_start < end, Appointment.status == AppointmentStatus.CONFIRMED)
        .order_by(Appointment.scheduled_start)
    )
    items = []
    for appt, job in result.all():
        items.append(
            {
                "job_reference": job.reference,
                "type": appt.appointment_type.value,
                "start": appt.scheduled_start.isoformat(),
                "start_uk": appt.scheduled_start.astimezone(uk_now().tzinfo).isoformat(),
                "postcode": appt.postcode,
            }
        )
    return items


async def tool_jobs_today(db: AsyncSession) -> dict[str, Any]:
    today = uk_today()
    start, end = utc_range_for_uk_day(today)
    items = await _appointments_between(db, start, end)
    return {
        "date": today.isoformat(),
        "date_label": uk_date_label(today),
        "timezone": "Europe/London",
        "appointments": items,
        "count": len(items),
    }


async def tool_jobs_tomorrow(db: AsyncSession) -> dict[str, Any]:
    tomorrow = uk_today() + timedelta(days=1)
    start, end = utc_range_for_uk_day(tomorrow)
    items = await _appointments_between(db, start, end)
    return {
        "date": tomorrow.isoformat(),
        "date_label": uk_date_label(tomorrow),
        "timezone": "Europe/London",
        "appointments": items,
        "count": len(items),
    }


async def tool_analytics_snapshot(db: AsyncSession) -> dict[str, Any]:
    snap = await build_analytics_snapshot(db, days=30)
    return {
        "period_days": snap.period_days,
        "enquiries": snap.enquiries,
        "quotations": snap.quotations,
        "quotes_accepted": snap.quotes_accepted,
        "revenue_collected_gbp": float(snap.revenue_collected_gbp),
        "quoted_revenue_gbp": float(snap.quoted_revenue_gbp),
        "quote_conversion_rate": snap.quote_conversion_rate,
    }


def _jsonable(obj: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in obj.items():
        if hasattr(v, "as_tuple"):
            out[k] = float(v)
        else:
            out[k] = v
    return out


async def tool_marketing_weekly_spend(db: AsyncSession) -> dict[str, Any]:
    return await weekly_spend_summary(db)


async def tool_marketing_director_plan(db: AsyncSession) -> dict[str, Any]:
    return await build_daily_marketing_plan(db)


async def tool_marketing_profitability(db: AsyncSession) -> dict[str, Any]:
    return await marketing_profitability_snapshot(db, days=30)


async def tool_marketing_integrations(db: AsyncSession) -> dict[str, Any]:
    return build_integration_centre()


async def tool_marketing_director_proactive(db: AsyncSession) -> dict[str, Any]:
    result = await run_daily_director_cycle(db, execute_research=False)
    await db.commit()
    return result


async def tool_marketing_launch_readiness(db: AsyncSession) -> dict[str, Any]:
    return assess_launch_readiness()


async def tool_marketing_pause_all(db: AsyncSession) -> dict[str, Any]:
    policy = await get_or_create_budget_policy(db)
    policy.emergency_pause_all = True
    platforms = await emergency_pause_connected_platforms()
    await db.commit()
    return {"emergency_pause_all": True, "platforms": platforms}


async def tool_marketing_vertical_queries(db: AsyncSession) -> dict[str, Any]:
    return {"queries": vertical_places_queries("retail_park", "Preston"), "verticals": list(PROSPECT_VERTICALS.keys())}


async def tool_marketing_content_calendar(db: AsyncSession) -> dict[str, Any]:
    return await calendar_view(db, days=7)


async def tool_marketing_capacity(db: AsyncSession) -> dict[str, Any]:
    global_cap, territories = await territory_demand_insights(db)
    return {
        "global": _jsonable(global_cap.__dict__),
        "territories": [_jsonable(t.__dict__) for t in territories if t.recommend_advertising][:5],
        "spare_slots": global_cap.spare_slots,
        "recommend_advertising": global_cap.recommend_advertising,
    }


async def tool_jobs_next_week(db: AsyncSession) -> dict[str, Any]:
    start, _ = utc_range_for_uk_day(uk_today())
    end, _ = utc_range_for_uk_day(uk_today() + timedelta(days=7))
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(Appointment.scheduled_start >= start, Appointment.scheduled_start < end, Appointment.status == AppointmentStatus.CONFIRMED)
        .order_by(Appointment.scheduled_start)
    )
    by_day: dict[str, int] = {}
    for appt, _ in result.all():
        day = appt.scheduled_start.astimezone(uk_now().tzinfo).date().isoformat()
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
        .where(Quotation.requires_approval.is_(True), Quotation.is_test.is_(False))
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
            Appointment.status == AppointmentStatus.CONFIRMED,
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
        .where(Enquiry.created_at >= since, Enquiry.stage == PipelineStage.NEW_ENQUIRY, Enquiry.is_test.is_(False))
    )
    count = result.scalar() or 0
    return {"last_7_days_new_enquiries": count}


async def tool_schedule_proposals(db: AsyncSession) -> dict[str, Any]:
    from app.models.crm import CustomerProperty
    from app.models.weather import ProductProfile
    from app.services.scheduling_engine import propose_two_stage_slots

    result = await db.execute(
        select(Job, CustomerProperty)
        .outerjoin(CustomerProperty, (CustomerProperty.id == Job.property_id) & (CustomerProperty.customer_id == Job.customer_id))
        .options(selectinload(Job.appointments))
        .where(Job.status.in_([JobStatus.RESTORATION_PENDING, JobStatus.PREPARATION_COMPLETED]))
        .order_by(Job.seven_day_target_date.asc().nulls_last())
        .limit(5)
    )
    profile = (await db.execute(select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1))).scalar_one_or_none()
    items = []
    for job, prop in result.all():
        item = {"reference": job.reference, "deadline": job.seven_day_target_date.isoformat() if job.seven_day_target_date else None}
        if any(a.appointment_type == AppointmentType.COATING and a.status in (AppointmentStatus.CONFIRMED, AppointmentStatus.PROVISIONAL, AppointmentStatus.IN_PROGRESS) for a in job.appointments):
            item["proposal"] = "Coating already scheduled"
        elif not profile or prop is None or prop.latitude is None or prop.longitude is None:
            item["proposal"] = "Missing product profile or property coordinates"
        else:
            try:
                _, slots = await propose_two_stage_slots(db, job=job, lat=float(prop.latitude), lon=float(prop.longitude), product_profile=profile, max_prep_slots=1)
                item["proposal"] = slots[0].start.astimezone(uk_now().tzinfo).isoformat() if slots else "No safe window found"
                if slots:
                    item["estimated_travel_minutes"] = slots[0].travel_minutes
                    item["weather_score"] = slots[0].weather_score
            except (ValueError, RuntimeError):
                item["proposal"] = "Scheduling or forecast unavailable"
        items.append(item)
    return {"proposals": items, "note": "Up to five priority jobs. Suggestions are independent, not reserved; recheck conflicts and live weather before confirming."}


TOOL_HANDLERS = {
    "jobs_today": tool_jobs_today,
    "jobs_tomorrow": tool_jobs_tomorrow,
    "jobs_next_week": tool_jobs_next_week,
    "wash_pending_coat": tool_wash_pending_coat,
    "pending_approvals": tool_pending_approvals,
    "quotations_awaiting": tool_quotations_awaiting,
    "rain_risk_coating": tool_rain_risk_appointments,
    "new_enquiries": tool_new_enquiries_count,
    "analytics_snapshot": tool_analytics_snapshot,
    "marketing_capacity": tool_marketing_capacity,
    "marketing_weekly_spend": tool_marketing_weekly_spend,
    "marketing_director_plan": tool_marketing_director_plan,
    "marketing_profitability": tool_marketing_profitability,
    "marketing_integrations": tool_marketing_integrations,
    "marketing_director_proactive": tool_marketing_director_proactive,
    "marketing_launch_readiness": tool_marketing_launch_readiness,
    "marketing_pause_all": tool_marketing_pause_all,
    "marketing_vertical_queries": tool_marketing_vertical_queries,
    "marketing_content_calendar": tool_marketing_content_calendar,
}