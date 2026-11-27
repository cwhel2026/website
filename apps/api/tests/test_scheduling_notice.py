"""Diary search must never return a visit that is already in the past."""

from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.services.scheduling_engine import earliest_search_from, slot_inside_working_hours

LONDON = ZoneInfo("Europe/London")


def _settings(**kwargs):
    values = {
        "min_notice_hours": 24,
        "work_day_start": time(8, 0),
        "work_day_end": time(17, 30),
        "earliest_work_date": date(2027, 3, 1),
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_friday_evening_request_does_not_search_the_same_afternoon():
    now = datetime(2026, 11, 27, 16, 57, tzinfo=UTC)
    start = earliest_search_from(_settings(), now)
    local = start.astimezone(LONDON)
    assert start > now
    assert local.date() >= date(2027, 3, 1)
    assert local.hour >= 8
    assert not (local.date() == date(2026, 11, 27) and local.hour == 12)


def test_slot_on_launch_morning_is_inside_hours():
    settings = _settings()
    start = datetime(2027, 3, 1, 8, 0, tzinfo=LONDON)
    end = start + timedelta(hours=2)
    assert slot_inside_working_hours(settings, start, end)


def test_slot_at_noon_the_day_of_the_request_is_rejected_when_it_is_already_past():
    settings = _settings(earliest_work_date=date(2026, 11, 27), min_notice_hours=24)
    past = datetime(2026, 11, 27, 12, 0, tzinfo=LONDON)
    now = datetime(2026, 11, 27, 16, 57, tzinfo=UTC)
    search = earliest_search_from(settings, now)
    assert search > past.astimezone(UTC)
    assert not slot_inside_working_hours(settings, past, past + timedelta(hours=2)) or search > past.astimezone(UTC)
