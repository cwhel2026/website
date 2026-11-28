"""Geographic clustering hints for route planning (haversine-based)."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Appointment, AppointmentStatus, Job
from app.services.geo import estimate_drive_minutes, haversine_km


@dataclass
class AppointmentClusterHint:
    appointment_id: str
    job_reference: str
    postcode: str | None
    scheduled_start: datetime
    drive_minutes_from_previous: int | None
    available_gap_minutes: int | None = None
    travel_conflict: bool | None = None


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
        .where(Appointment.scheduled_start >= day_start, Appointment.scheduled_start < day_end, Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS]))
        .order_by(Appointment.scheduled_start)
    )
    items = list(result.all())
    hints: list[AppointmentClusterHint] = []
    prev_lat, prev_lon = base_lat, base_lon
    previous_end = None
    for appt, job in items:
        lat, lon = appt.latitude, appt.longitude
        drive = None
        if all(v is not None for v in (prev_lat, prev_lon, lat, lon)):
            drive = estimate_drive_minutes(haversine_km(float(prev_lat), float(prev_lon), float(lat), float(lon)))
        gap = int((appt.scheduled_start - previous_end).total_seconds() / 60) if previous_end is not None else None
        hints.append(
            AppointmentClusterHint(
                appointment_id=str(appt.id),
                job_reference=job.reference,
                postcode=appt.postcode,
                scheduled_start=appt.scheduled_start,
                drive_minutes_from_previous=drive,
                available_gap_minutes=gap,
                travel_conflict=(gap < drive) if gap is not None and drive is not None else None,
            )
        )
        prev_lat, prev_lon = lat, lon
        previous_end = appt.scheduled_end
    return hints