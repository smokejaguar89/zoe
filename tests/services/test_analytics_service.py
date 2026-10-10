import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService, TimeGroup


def _snapshot(timestamp: datetime, temperature: float) -> SensorSnapshot:
    return SensorSnapshot(
        temperature=temperature,
        humidity=40.0,
        light=100.0,
        moisture=0.5,
        pressure=1005.0,
        timestamp=timestamp,
    )


def test_round_down_day_starts_at_zurich_midnight() -> None:
    # Arrange: 23:30 UTC on 9 April is 01:30 on 10 April in Zurich (CEST)
    service = AnalyticsService(snapshot_repository=MagicMock())
    timestamp = datetime(2026, 4, 9, 23, 30, tzinfo=timezone.utc)

    # Act
    bucket = service.round_down(timestamp, timedelta(days=1))

    # Assert: midnight on 10 April in Zurich is 22:00 UTC on 9 April
    assert bucket == datetime(2026, 4, 9, 22, 0, tzinfo=timezone.utc)


def test_get_last_week_snapshots_groups_by_local_day() -> None:
    # Arrange: both readings fall on 10 April in Zurich, but on different
    # UTC days
    snapshot_repository = MagicMock()
    snapshot_repository.list_between = MagicMock(
        return_value=[
            _snapshot(datetime(2026, 4, 9, 23, 0, tzinfo=timezone.utc), 20.0),
            _snapshot(datetime(2026, 4, 10, 8, 0, tzinfo=timezone.utc), 24.0),
        ]
    )
    service = AnalyticsService(snapshot_repository=snapshot_repository)

    # Act
    snapshots = asyncio.run(service.get_last_week_snapshots(TimeGroup.DAY))

    # Assert
    assert len(snapshots) == 1
    assert snapshots[0].temperature == 22.0
    assert snapshots[0].timestamp == datetime(
        2026, 4, 9, 22, 0, tzinfo=timezone.utc
    )


def test_get_last_week_snapshots_queries_with_aware_utc_bounds() -> None:
    # Arrange
    snapshot_repository = MagicMock()
    snapshot_repository.list_between = MagicMock(return_value=[])
    service = AnalyticsService(snapshot_repository=snapshot_repository)

    # Act
    asyncio.run(service.get_last_week_snapshots(TimeGroup.HOUR))

    # Assert
    kwargs = snapshot_repository.list_between.call_args.kwargs
    assert kwargs["start_time"].tzinfo == timezone.utc
    assert kwargs["end_time"] - kwargs["start_time"] == timedelta(days=7)
