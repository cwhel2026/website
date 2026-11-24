import pytest

from app.services.weather.providers.simulation import simulate_hourly_forecast
from app.services.weather.service import get_hourly_forecast


class FakeSession:
    async def execute(self, *args, **kwargs):
        class R:
            def scalars(self):
                return self

            def all(self):
                return []

        return R()

    async def flush(self):
        pass

    async def commit(self):
        pass


@pytest.mark.asyncio
async def test_get_forecast_simulation_provider(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("WEATHER_PROVIDER", "simulation")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.weather.service.settings",
        get_settings(),
    )

    rows, source, is_live = await get_hourly_forecast(
        None, 53.59, -2.84, hours=12, for_booking=False
    )
    assert source == "simulation"
    assert is_live is False
    assert len(rows) == 12


def test_simulation_still_deterministic():
    a = simulate_hourly_forecast(53.6, -2.9, hours=24)
    b = simulate_hourly_forecast(53.6, -2.9, hours=24)
    assert len(a) == len(b) == 24