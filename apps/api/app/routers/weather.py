import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.jobs import Appointment, AppointmentType
from app.models.user import User
from app.models.weather import AppointmentWeatherCheck, ProductProfile, WorkActivity
from app.services.geocode import geocode_postcode
from app.services.weather.service import get_hourly_forecast
from app.services.weather_engine import score_window, suitability_to_json

router = APIRouter(prefix="/weather", tags=["weather"])
settings = get_settings()


class ForecastHourOut(BaseModel):
    forecast_time: datetime
    temp_c: float
    precipitation_mm: float
    precip_probability_pct: int
    wind_mph: int
    humidity_pct: int | None = None
    source: str
    is_live: bool


class WeatherCheckOut(BaseModel):
    appointment_id: UUID
    activity: str
    suitability_score: int
    is_safe: bool
    requires_on_site_confirmation: bool
    forecast_source: str
    forecast_is_live: bool
    detail: dict


@router.get("/forecast", response_model=list[ForecastHourOut])
async def get_forecast(
    db: Annotated[AsyncSession, Depends(get_db)],
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    postcode: str | None = Query(None, min_length=2, max_length=10),
    hours: int = Query(48, le=120),
    for_booking: bool = Query(False),
) -> list[ForecastHourOut]:
    if postcode:
        point = await geocode_postcode(postcode)
        lat, lon = point.latitude, point.longitude
    if lat is None or lon is None:
        raise HTTPException(400, "Provide postcode or lat/lon")

    try:
        rows, source, is_live = await get_hourly_forecast(
            db, lat, lon, hours=hours, for_booking=for_booking
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    await db.commit()
    return [
        ForecastHourOut(
            forecast_time=r.forecast_time,
            temp_c=float(r.temp_c),
            precipitation_mm=float(r.precipitation_mm),
            precip_probability_pct=r.precip_probability_pct,
            wind_mph=r.wind_mph,
            humidity_pct=r.humidity_pct,
            source=source,
            is_live=is_live,
        )
        for r in rows
    ]


@router.get("/status")
async def weather_status() -> dict:
    return {
        "provider": settings.weather_provider,
        "simulation_fallback": settings.weather_simulation_fallback,
        "simulation_allowed_for_booking": settings.weather_allow_simulation_for_booking,
    }


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
    forecast, source, is_live = await get_hourly_forecast(
        db, lat, lon, hours=72, for_booking=True
    )
    result = score_window(
        activity,
        profile,
        forecast,
        appt.scheduled_start,
        appt.duration_minutes / 60,
    )
    appt.weather_suitable = result.is_safe if is_live else None
    appt.weather_notes = suitability_to_json(result)
    db.add(
        AppointmentWeatherCheck(
            appointment_id=appointment_id,
            activity=activity,
            suitability_score=result.score,
            is_safe=result.is_safe,
            requires_on_site_confirmation=result.requires_on_site_confirmation,
            detail_json=json.dumps({**result.detail, "source": source, "is_live": is_live}),
        )
    )
    await db.commit()
    return WeatherCheckOut(
        appointment_id=appointment_id,
        activity=activity.value,
        suitability_score=result.score,
        is_safe=result.is_safe,
        requires_on_site_confirmation=result.requires_on_site_confirmation,
        forecast_source=source,
        forecast_is_live=is_live,
        detail={**result.detail, "source": source, "is_live": is_live},
    )