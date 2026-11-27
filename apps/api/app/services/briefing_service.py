import json
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import ApprovalRequest, ApprovalStatus
from app.models.briefings import BriefingKind, BriefingRecord
from app.models.jobs import Appointment, Job, AppointmentStatus
from app.models.quotation import Quotation, QuotationStatus
from app.services.assistant_tools import (
    tool_jobs_tomorrow,
    tool_pending_approvals,
    tool_wash_pending_coat,
)
from app.services.weather.service import get_hourly_forecast


async def generate_briefing(db: AsyncSession, kind: BriefingKind) -> BriefingRecord:
    payload: dict = {"kind": kind.value, "generated_at": datetime.now(UTC).isoformat()}

    if kind == BriefingKind.MORNING:
        payload["tomorrow"] = await tool_jobs_tomorrow(db)
        payload["wash_pending"] = await tool_wash_pending_coat(db)
        payload["approvals"] = await tool_pending_approvals(db)
        try:
            forecast, source, is_live = await get_hourly_forecast(db, 53.5977, -2.8407, hours=24)
        except (RuntimeError, ValueError):
            forecast, source, is_live = [], "unavailable", False
        payload["weather_hq"] = {
            "source": source,
            "is_live": is_live,
            "samples": [
                {
                    "time": f.forecast_time.isoformat(),
                    "temp_c": float(f.temp_c),
                    "rain_pct": f.precip_probability_pct,
                }
                for f in forecast[8:18]
            ],
        }
        pending_quotes = await db.execute(
            select(func.count()).select_from(Quotation).where(Quotation.status == QuotationStatus.PROVISIONAL, Quotation.is_test.is_(False))
        )
        payload["provisional_quotes_outstanding"] = pending_quotes.scalar() or 0
    else:
        today_start = datetime.now(ZoneInfo("Europe/London")).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
        completed = await db.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.updated_at >= today_start)
        )
        payload["jobs_touched_today"] = completed.scalar() or 0
        payload["tomorrow_preview"] = await tool_jobs_tomorrow(db)
        since = datetime.now(UTC) - timedelta(hours=24)
        new_approvals = await db.execute(
            select(func.count())
            .select_from(ApprovalRequest)
            .where(ApprovalRequest.created_at >= since)
        )
        payload["new_approval_requests_24h"] = new_approvals.scalar() or 0

        tomorrow = datetime.now(ZoneInfo("Europe/London")).date() + timedelta(days=1)
        appt_start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=ZoneInfo("Europe/London"))
        appt_end = appt_start + timedelta(days=1)
        count = await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.scheduled_start >= appt_start, Appointment.scheduled_start < appt_end, Appointment.status == AppointmentStatus.CONFIRMED)
        )
        payload["tomorrow_appointment_count"] = count.scalar() or 0

    record = BriefingRecord(kind=kind, content_json=json.dumps(payload))
    db.add(record)
    await db.flush()
    return record