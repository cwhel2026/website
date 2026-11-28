import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.weather import ProductProfile, WorkActivity
from app.services.weather.providers.simulation import simulate_hourly_forecast
from app.services.weather.types import HourForecast

__all__ = ["HourForecast", "simulate_hourly_forecast", "score_window", "suitability_to_json"]


@dataclass
class SuitabilityResult:
    score: int
    is_safe: bool
    requires_on_site_confirmation: bool
    detail: dict


def score_window(
    activity: WorkActivity,
    profile: ProductProfile,
    hours: list[HourForecast],
    window_start: datetime,
    duration_hours: float,
) -> SuitabilityResult:
    if not 0 < duration_hours <= 24:
        return SuitabilityResult(0, False, True, {"reason": "invalid_duration"})
    window_end = window_start + timedelta(hours=duration_hours)
    first_hour = window_start.replace(minute=0, second=0, microsecond=0)
    expected = set()
    cursor = first_hour
    while cursor < window_end:
        expected.add(cursor)
        cursor += timedelta(hours=1)
    selected = [
        h
        for h in hours
        if first_hour <= h.forecast_time < window_end
    ]
    if not selected or not expected.issubset({h.forecast_time for h in selected}):
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
    hard_fail = any(r in ("temp_below_min", "temp_above_max", "wind_too_high", "wind_unsafe") for r in reasons)
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