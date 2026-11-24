import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.weather import ProductProfile, WorkActivity


@dataclass
class HourForecast:
    forecast_time: datetime
    temp_c: Decimal
    precipitation_mm: Decimal
    precip_probability_pct: int
    wind_mph: int
    humidity_pct: int


@dataclass
class SuitabilityResult:
    score: int
    is_safe: bool
    requires_on_site_confirmation: bool
    detail: dict


def simulate_hourly_forecast(
    latitude: float, longitude: float, hours: int = 48
) -> list[HourForecast]:
    """Deterministic simulation for development — clearly not live MET data."""
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


def score_window(
    activity: WorkActivity,
    profile: ProductProfile,
    hours: list[HourForecast],
    window_start: datetime,
    duration_hours: float,
) -> SuitabilityResult:
    window_end = window_start + timedelta(hours=duration_hours)
    selected = [
        h
        for h in hours
        if window_start <= h.forecast_time < window_end
    ]
    if not selected:
        return SuitabilityResult(0, False, True, {"reason": "no_forecast_data"})

    reasons: list[str] = []
    score = 100

    for h in selected:
        if activity == WorkActivity.COATING:
            if h.temp_c < profile.min_application_temp_c:
                reasons.append("temp_below_min")
                score -= 40
            if h.temp_c > profile.max_application_temp_c:
                reasons.append("temp_above_max")
                score -= 35
            if h.precipitation_mm > Decimal("0.1") or h.precip_probability_pct > 40:
                reasons.append("rain_risk")
                score -= 50
            if h.wind_mph > profile.max_wind_mph:
                reasons.append("wind_too_high")
                score -= 30
        elif activity == WorkActivity.WASHING:
            # Washing prefers wet/overcast but must remain safe
            if h.wind_mph > profile.max_wind_mph + 10:
                reasons.append("wind_unsafe")
                score -= 45
            if h.precip_probability_pct > 90:
                reasons.append("heavy_rain")
                score -= 25
            else:
                score += 5  # slight preference for overcast

    score = max(0, min(100, score))
    hard_fail = any(r in ("temp_below_min", "temp_above_max", "wind_too_high") for r in reasons)
    if activity == WorkActivity.COATING and any(r == "rain_risk" for r in reasons):
        hard_fail = True

    is_safe = score >= 60 and not hard_fail
    return SuitabilityResult(
        score=score,
        is_safe=is_safe,
        requires_on_site_confirmation=True,
        detail={
            "reasons": reasons,
            "profile": profile.slug,
            "hours_evaluated": len(selected),
        },
    )


def suitability_to_json(result: SuitabilityResult) -> str:
    return json.dumps(result.detail)