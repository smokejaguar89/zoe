from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Stores aware datetimes as naive UTC and returns them as aware UTC.

    SQLite has no timezone support, so this keeps every stored value in one
    timezone and rejects naive datetimes rather than guessing what they mean.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: Optional[datetime], dialect
    ) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError(
                f"Naive datetime {value!r} cannot be stored; use UTC."
            )
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(
        self, value: Optional[datetime], dialect
    ) -> Optional[datetime]:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)
