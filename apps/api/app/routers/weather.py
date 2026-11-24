from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.jobs import Appointment, AppointmentType
from app.models.user import User
from app.models.weather import ProductProfile, WorkActivity
from app.services.weather_engine import (
    simulate_hourly_forecast,
    score_window,
    suitability_to_json,
)

router = APIRouter(prefix="/weather", tags=["weather"])


class ForecastHourOut(BaseModel):
    forecast_time: datetime
    temp_c: float
    precipitation_mm: float
    precip_probability_pct: int
    wind_mph: int
    source: str = "simulation"


class WeatherCheckOut(BaseModel):
    appointment_id: UUID
    activity: str
    suitability_score: int
    is_safe: bool
    requires_on_site_confirmation: bool
    detail: dict


@router.get("/forecast", response_model=list[ForecastHourOut])
async def get_forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    hours: int = Query(48, le=120),
) -> list[ForecastHourOut]:
    rows = simulate_hourly_forecast(lat, lon, hours=hours)
    return [
        ForecastHourOut(
            forecast_time=r.forecast_time,
            temp_c=float(r.temp_c),
            precipitation_mm=float(r.precipitation_mm),
            precip_probability_pct=r.precip_probability_pct,
            wind_mph=r.wind_mph,
        )
        for r in rows
    ]


@router.post("/check/{appointment_id}", response_model=WeatherCheckOut)
async def check_appointment_weather(
    appointment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> WeatherCheckOut:
    appt = await db.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(404, "Appointment not found")
    profile_result = await db.execute(
        select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(500, "No product profile")
    lat = appt.latitude or 53.65
    lon = appt.longitude or -2.95
    activity = (
        WorkActivity.WASHING
        if appt.appointment_type == AppointmentType.PREPARATION
        else WorkActivity.COATING
    )
    forecast = simulate_hourly_forecast(lat, lon, hours=72)
    result = score_window(
        activity,
        profile,
        forecast,
        appt.scheduled_start,
        appt.duration_minutes / 60,
    )
    appt.weather_suitable = result.is_safe
    appt.weather_notes = suitability_to_json(result)
    await db.commit()
    return WeatherCheckOut(
        appointment_id=appointment_id,
        activity=activity.value,
        suitability_score=result.score,
        is_safe=result.is_safe,
        requires_on_site_confirmation=result.requires_on_site_confirmation,
        detail=result.detail,
    )