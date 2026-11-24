import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.weather.types import HourForecast


def simulate_hourly_forecast(
    latitude: float, longitude: float, hours: int = 48
) -> list[HourForecast]:
    """Deterministic simulation — must not authorise customer bookings when live data required."""
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    seed = abs(int((latitude * 1000) + (longitude * 100))) % 97
    rows: list[HourForecast] = []
    for i in range(hours):
        t = now + timedelta(hours=i)
        wave = math.sin((i + seed) / 6.0)
        temp = Decimal(str(round(11 + 6 * wave, 1)))
        precip = Decimal("0.0")
        prob = 0
        if wave < -0.35:
            precip = Decimal(str(round(0.4 + abs(wave), 2)))
            prob = min(95, int(40 + abs(wave) * 60))
        wind = int(8 + abs(wave) * 10)
        humidity = int(55 + wave * 15)
        rows.append(
            HourForecast(
                forecast_time=t,
                temp_c=temp,
                precipitation_mm=precip,
                precip_probability_pct=prob,
                wind_mph=wind,
                humidity_pct=humidity,
            )
        )
    return rows