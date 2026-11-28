from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin, get_current_admin_writer
from app.database import get_db
from app.models.jobs import Appointment, Job
from app.models.scheduling import OwnerCalendarBlock, RegionalWorkingDay, SchedulingSettings
from app.services.scheduling_engine import find_conflicts, get_scheduling_settings
from app.services.scheduling_geo import daily_route_hints
from app.models.user import User

router = APIRouter(prefix="/calendar", tags=["calendar"])


class AppointmentCalendarOut(BaseModel):
    id: UUID
    job_id: UUID
    job_reference: str
    appointment_type: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    postcode: str | None


class CalendarBlockIn(BaseModel):
    title: str
    block_start: datetime
    block_end: datetime
    is_unavailable: bool = True


class RegionalDayOut(BaseModel):
    territory_id: UUID
    work_date: str
    focus: str | None


@router.get("/appointments", response_model=list[AppointmentCalendarOut])
async def list_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
) -> list[AppointmentCalendarOut]:
    if from_dt.tzinfo is None or to_dt.tzinfo is None or not from_dt < to_dt <= from_dt + timedelta(days=93):
        raise HTTPException(422, "Invalid calendar range")
    result = await db.execute(
        select(Appointment, Job)
        .join(Job)
        .where(Appointment.scheduled_end > from_dt, Appointment.scheduled_start < to_dt)
        .order_by(Appointment.scheduled_start)
    )
    return [
        AppointmentCalendarOut(
            id=appt.id,
            job_id=job.id,
            job_reference=job.reference,
            appointment_type=appt.appointment_type.value,
            status=appt.status.value,
            scheduled_start=appt.scheduled_start,
            scheduled_end=appt.scheduled_end,
            postcode=appt.postcode,
        )
        for appt, job in result.all()
    ]


@router.post("/blocks")
async def add_block(
    body: CalendarBlockIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_writer)],
) -> dict[str, str]:
    if body.block_start.tzinfo is None or body.block_end.tzinfo is None or body.block_end <= body.block_start:
        raise HTTPException(422, "Invalid calendar block")
    await db.execute(select(SchedulingSettings).with_for_update())
    if body.is_unavailable and await find_conflicts(db, body.block_start, body.block_end):
        raise HTTPException(409, "Existing diary commitments conflict with this block")
    db.add(
        OwnerCalendarBlock(
            title=body.title,
            block_start=body.block_start,
            block_end=body.block_end,
            is_unavailable=body.is_unavailable,
        )
    )
    await db.commit()
    return {"message": "Block created"}


@router.get("/regional-days", response_model=list[RegionalDayOut])
async def regional_days(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[RegionalDayOut]:
    result = await db.execute(
        select(RegionalWorkingDay).order_by(RegionalWorkingDay.work_date).limit(30)
    )
    return [
        RegionalDayOut(
            territory_id=r.territory_id,
            work_date=r.work_date.isoformat(),
            focus=r.focus,
        )
        for r in result.scalars().all()
    ]

@router.get("/route-review")
async def route_review(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    day: date,
) -> dict:
    london = ZoneInfo("Europe/London")
    start = datetime.combine(day, time.min, tzinfo=london)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=london)
    settings = await get_scheduling_settings(db)
    hints = await daily_route_hints(db, day_start=start, day_end=end, base_lat=settings.base_latitude, base_lon=settings.base_longitude)
    return {"day": day.isoformat(), "method": "geographic_estimate_not_live_traffic", "appointments": [h.__dict__ for h in hints]}
