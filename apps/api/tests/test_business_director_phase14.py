from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.business_director import director_signals, run_business_director_scan, SIGNAL_ACTIONS


@pytest.mark.asyncio
async def test_director_signals_use_database_counts():
    db = AsyncMock()
    db.scalar.side_effect = [2, 0, 3, 4, 1]
    signals = await director_signals(db)
    assert signals == dict(zip(SIGNAL_ACTIONS, [2, 0, 3, 4, 1]))
    assert db.scalar.await_count == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", [None, SimpleNamespace(is_paused=True, emergency_stop=False), SimpleNamespace(is_paused=False, emergency_stop=True)])
async def test_director_stops_before_generating_tasks(profile):
    db = AsyncMock()
    db.scalar.return_value = profile
    assert await run_business_director_scan(db) == []
    db.flush.assert_not_awaited()
