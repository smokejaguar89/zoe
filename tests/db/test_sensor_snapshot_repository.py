from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import StatementError

from app.db.repositories.sensor_snapshot_repository import (
    SensorSnapshotRepository,
)
from app.utils.clock import LOCAL_TIMEZONE
from tests.db.helpers import make_snapshot


@pytest.fixture
def repository(database):
    return SensorSnapshotRepository(engine=database.engine)


def test_timestamps_round_trip_as_aware_utc(repository) -> None:
    # Arrange
    zurich_time = datetime(2026, 4, 9, 14, 30, tzinfo=LOCAL_TIMEZONE)

    # Act
    repository.add(make_snapshot(zurich_time))
    [stored] = repository.list_between(
        start_time=zurich_time - timedelta(hours=1),
        end_time=zurich_time + timedelta(hours=1),
    )

    # Assert
    assert stored.timestamp == zurich_time
    assert stored.timestamp.tzinfo == timezone.utc
    assert stored.timestamp.hour == 12


def test_saving_naive_datetime_is_rejected(repository) -> None:
    with pytest.raises(StatementError, match="Naive datetime"):
        repository.add(make_snapshot(datetime(2026, 4, 9, 14, 30)))


def test_list_between_compares_instants_not_wall_clock(repository) -> None:
    # Arrange: 12:30 UTC is 14:30 in Zurich
    repository.add(
        make_snapshot(datetime(2026, 4, 9, 12, 30, tzinfo=timezone.utc))
    )

    # Act
    in_range = repository.list_between(
        start_time=datetime(2026, 4, 9, 14, 0, tzinfo=LOCAL_TIMEZONE),
        end_time=datetime(2026, 4, 9, 15, 0, tzinfo=LOCAL_TIMEZONE),
    )
    out_of_range = repository.list_between(
        start_time=datetime(2026, 4, 9, 12, 0, tzinfo=LOCAL_TIMEZONE),
        end_time=datetime(2026, 4, 9, 13, 0, tzinfo=LOCAL_TIMEZONE),
    )

    # Assert
    assert len(in_range) == 1
    assert out_of_range == []


def test_list_between_returns_oldest_first(repository) -> None:
    # Arrange: added out of order
    for hour in (14, 9, 11):
        repository.add(
            make_snapshot(datetime(2026, 4, 9, hour, tzinfo=timezone.utc))
        )

    # Act
    snapshots = repository.list_between(
        start_time=datetime(2026, 4, 9, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 10, tzinfo=timezone.utc),
    )

    # Assert
    assert [s.timestamp.hour for s in snapshots] == [9, 11, 14]
