from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import httpx

from app.services.weather.types import HourForecast

UK = ZoneInfo("Europe/London")

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


async def fetch_openmeteo_hourly(latitude: float, longitude: float, hours: int = 48) -> list[HourForecast]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation,precipitation_probability,wind_speed_10m,relative_humidity_2m",
        "forecast_days": min(7, (hours // 24) + 1),
        "timezone": "Europe/London",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(OPEN_METEO, params=params)
        response.raise_for_status()
        payload = response.json()

    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    precs = hourly.get("precipitation") or []
    probs = hourly.get("precipitation_probability") or []
    winds = hourly.get("wind_speed_10m") or []
    hums = hourly.get("relative_humidity_2m") or []

    rows: list[HourForecast] = []
    for i, ts in enumerate(times[:hours]):
        forecast_time = datetime.fromisoformat(ts).replace(tzinfo=UK).astimezone(UTC)
        wind_kmh = float(winds[i]) if i < len(winds) else 0.0
        wind_mph = int(round(wind_kmh * 0.621371))
        rows.append(
            HourForecast(
                forecast_time=forecast_time,
                temp_c=Decimal(str(round(float(temps[i]), 1))),
                precipitation_mm=Decimal(str(round(float(precs[i]), 2))),
                precip_probability_pct=int(probs[i]) if i < len(probs) else 0,
                wind_mph=wind_mph,
                humidity_pct=int(hums[i]) if i < len(hums) else 50,
            )
        )
    return rows


def fetch_openmeteo_hourly_sync(latitude: float, longitude: float, hours: int = 48) -> list[HourForecast]:
    """Sync wrapper for Celery workers."""
    import asyncio

    return asyncio.run(fetch_openmeteo_hourly(latitude, longitude, hours=hours))