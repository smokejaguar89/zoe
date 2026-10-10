"""Time handling rule: datetimes are always timezone-aware UTC inside the app
and the database. Convert to LOCAL_TIMEZONE only at the edges (display,
filenames and scheduling)."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_TIMEZONE = ZoneInfo("Europe/Zurich")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_local(value: datetime) -> datetime:
    return value.astimezone(LOCAL_TIMEZONE)
