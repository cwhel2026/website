from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.weather import ProductProfile
from app.services.weather_engine import (
    WorkActivity,
    score_window,
    simulate_hourly_forecast,
)


def _profile() -> ProductProfile:
    return ProductProfile(
        name="test",
        slug="test",
        min_application_temp_c=Decimal("10"),
        max_application_temp_c=Decimal("28"),
        min_drying_hours=24,
        rain_free_window_hours=4,
        max_wind_mph=20,
        is_active=True,
    )


def test_simulation_returns_48_hours():
    rows = simulate_hourly_forecast(53.6, -2.9, hours=48)
    assert len(rows) == 48
    assert rows[0].forecast_time.tzinfo is not None


def test_coating_unsafe_in_cold_window():
    profile = _profile()
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    hours = [
        type("H", (), {
            "forecast_time": start + timedelta(hours=i),
            "temp_c": Decimal("5"),
            "precipitation_mm": Decimal("0"),
            "precip_probability_pct": 0,
            "wind_mph": 5,
            "humidity_pct": 50,
        })()
        for i in range(4)
    ]
    result = score_window(WorkActivity.COATING, profile, hours, start, 4)
    assert result.is_safe is False
    assert "temp_below_min" in result.detail.get("reasons", [])


def test_washing_scores_when_overcast_simulated():
    profile = _profile()
    forecast = simulate_hourly_forecast(53.59, -2.84, hours=24)
    start = forecast[10].forecast_time
    result = score_window(WorkActivity.WASHING, profile, forecast, start, 2)
    assert 0 <= result.score <= 100