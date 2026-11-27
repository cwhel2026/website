"""Regression tests: simulated/stale cache must not satisfy booking weather checks."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.weather.service import get_hourly_forecast
from app.services.weather.types import HourForecast


def _hour_row(t: datetime) -> HourForecast:
    return HourForecast(
        forecast_time=t,
        temp_c=Decimal("12"),
        precipitation_mm=Decimal("0"),
        precip_probability_pct=5,
        wind_mph=8,
        humidity_pct=70,
    )


@pytest.mark.asyncio
async def test_booking_rejects_simulated_cache(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("WEATHER_PROVIDER", "openmeteo")
    monkeypatch.setenv("WEATHER_ALLOW_SIMULATION_FOR_BOOKING", "false")
    get_settings.cache_clear()
    monkeypatch.setattr("app.services.weather.service.settings", get_settings())

    simulated_cache = (
        [_hour_row(datetime.now(UTC) + timedelta(hours=i)) for i in range(24)],
        "simulation",
        False,
    )

    async def fake_load_cache(*_args, **_kwargs):
        return simulated_cache

    fetch_mock = AsyncMock(side_effect=RuntimeError("live down"))
    monkeypatch.setattr("app.services.weather.service._load_cache", fake_load_cache)
    monkeypatch.setattr("app.services.weather.service.fetch_openmeteo_hourly", fetch_mock)

    with pytest.raises(RuntimeError, match="live down|booking weather checks blocked|Live weather unavailable"):
        await get_hourly_forecast(None, 53.59, -2.84, hours=24, for_booking=True)


@pytest.mark.asyncio
async def test_non_booking_allows_simulated_cache(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("WEATHER_PROVIDER", "simulation")
    get_settings.cache_clear()
    monkeypatch.setattr("app.services.weather.service.settings", get_settings())

    simulated_cache = (
        [_hour_row(datetime.now(UTC) + timedelta(hours=i)) for i in range(24)],
        "simulation",
        False,
    )

    async def fake_load_cache(*_args, **_kwargs):
        return simulated_cache

    monkeypatch.setattr("app.services.weather.service._load_cache", fake_load_cache)

    rows, source, is_live = await get_hourly_forecast(
        object(), 53.59, -2.84, hours=24, for_booking=False
    )
    assert source == "simulation"
    assert is_live is False
    assert len(rows) == 24

@pytest.mark.asyncio
async def test_schedule_proposals_reject_simulated_forecast(monkeypatch):
    from types import SimpleNamespace
    from datetime import time
    from app.services import scheduling_engine as engine
    settings = SimpleNamespace(min_notice_hours=24, work_day_start=time(8), work_day_end=time(17, 30), earliest_work_date=None, base_latitude=53.59, base_longitude=-2.84, travel_buffer_minutes=10)
    monkeypatch.setattr(engine, "get_scheduling_settings", AsyncMock(return_value=settings))
    monkeypatch.setattr(engine, "get_hourly_forecast", AsyncMock(return_value=([], "simulation", False)))
    with pytest.raises(RuntimeError, match="Live forecast required"):
        await engine.propose_two_stage_slots(object(), lat=53.59, lon=-2.84, product_profile=None)
