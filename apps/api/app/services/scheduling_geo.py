"""Geographic clustering hints for route planning (haversine-based)."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Appointment, Job
from app.services.geo import estimate_drive_minutes, haversine_km


@dataclass
class AppointmentClusterHint:
    appointment_id: str
    job_reference: str
    postcode: str | None
    scheduled_start: datetime
    drive_minutes_from_previous: int


async def daily_route_hints(
    db: AsyncSession,
    *,
    day_start: datetime,
    day_end: datetime,
    base_lat: float,
    base_lon: float,
) -> list[AppointmentClusterHint]:
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(Appointment.scheduled_start >= day_start, Appointment.scheduled_start < day_end)
        .order_by(Appointment.scheduled_start)
    )
    items = list(result.all())
    hints: list[AppointmentClusterHint] = []
    prev_lat, prev_lon = base_lat, base_lon
    for appt, job in items:
        lat = appt.latitude or base_lat
        lon = appt.longitude or base_lon
        km = haversine_km(prev_lat, prev_lon, lat, lon)
        drive = estimate_drive_minutes(km)
        hints.append(
            AppointmentClusterHint(
                appointment_id=str(appt.id),
                job_reference=job.reference,
                postcode=appt.postcode,
                scheduled_start=appt.scheduled_start,
                drive_minutes_from_previous=drive,
            )
        )
        prev_lat, prev_lon = lat, lon
    return hints