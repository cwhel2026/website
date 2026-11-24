from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.weather import WeatherForecastHour
from app.services.weather.providers.openmeteo import fetch_openmeteo_hourly
from app.services.weather.providers.simulation import simulate_hourly_forecast
from app.services.weather.types import HourForecast

settings = get_settings()
CACHE_TTL_MINUTES = 55


async def get_hourly_forecast(
    db: AsyncSession | None,
    latitude: float,
    longitude: float,
    *,
    hours: int = 48,
    for_booking: bool = False,
) -> tuple[list[HourForecast], str, bool]:
    """
    Returns (forecast, source, is_live).
    Simulated data is never returned for booking decisions unless explicitly allowed.
    """
    provider = settings.weather_provider.lower()
    lat_r = round(latitude, 4)
    lon_r = round(longitude, 4)

    if db is not None:
        cached = await _load_cache(db, lat_r, lon_r, hours)
        if cached:
            return cached

    live_error: str | None = None
    if provider in {"openmeteo", "auto"}:
        try:
            rows = await fetch_openmeteo_hourly(latitude, longitude, hours=hours)
            if db is not None:
                await _persist_cache(db, lat_r, lon_r, rows, source="openmeteo")
            return rows, "openmeteo", True
        except Exception as exc:
            live_error = str(exc)

    if for_booking and not settings.weather_allow_simulation_for_booking:
        raise RuntimeError(
            live_error or "Live weather unavailable — booking weather checks blocked (simulation not permitted)."
        )

    if provider == "simulation" or settings.weather_simulation_fallback:
        rows = simulate_hourly_forecast(latitude, longitude, hours=hours)
        if db is not None:
            await _persist_cache(db, lat_r, lon_r, rows, source="simulation")
        return rows, "simulation", False

    raise RuntimeError(live_error or "Weather provider unavailable")


async def _load_cache(
    db: AsyncSession, lat: float, lon: float, hours: int
) -> tuple[list[HourForecast], str, bool] | None:
    since = datetime.now(UTC) - timedelta(minutes=CACHE_TTL_MINUTES)
    result = await db.execute(
        select(WeatherForecastHour)
        .where(
            WeatherForecastHour.latitude == Decimal(str(lat)),
            WeatherForecastHour.longitude == Decimal(str(lon)),
            WeatherForecastHour.fetched_at >= since,
        )
        .order_by(WeatherForecastHour.forecast_time)
        .limit(hours)
    )
    rows = list(result.scalars().all())
    if len(rows) < min(hours, 12):
        return None
    source = rows[0].source
    is_live = source != "simulation"
    forecast = [
        HourForecast(
            forecast_time=r.forecast_time,
            temp_c=r.temp_c,
            precipitation_mm=r.precipitation_mm,
            precip_probability_pct=r.precip_probability_pct,
            wind_mph=r.wind_mph,
            humidity_pct=r.humidity_pct,
        )
        for r in rows[:hours]
    ]
    return forecast, source, is_live


async def _persist_cache(
    db: AsyncSession, lat: float, lon: float, rows: list[HourForecast], *, source: str
) -> None:
    await db.execute(
        delete(WeatherForecastHour).where(
            WeatherForecastHour.latitude == Decimal(str(lat)),
            WeatherForecastHour.longitude == Decimal(str(lon)),
        )
    )
    now = datetime.now(UTC)
    for r in rows:
        db.add(
            WeatherForecastHour(
                latitude=Decimal(str(lat)),
                longitude=Decimal(str(lon)),
                forecast_time=r.forecast_time,
                temp_c=r.temp_c,
                precipitation_mm=r.precipitation_mm,
                precip_probability_pct=r.precip_probability_pct,
                wind_mph=r.wind_mph,
                humidity_pct=r.humidity_pct,
                source=source,
                fetched_at=now,
            )
        )
    await db.flush()