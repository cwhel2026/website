"""UK-local business calendar helpers for scheduling and assistant tools."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")


def uk_now() -> datetime:
    return datetime.now(UK)


def uk_today() -> date:
    return uk_now().date()


def utc_range_for_uk_day(day: date) -> tuple[datetime, datetime]:
    """Return UTC [start, end) bounds for a calendar day in Europe/London."""
    start_local = datetime.combine(day, time.min, tzinfo=UK)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def uk_date_label(day: date) -> str:
    return day.strftime("%A %d %B %Y")