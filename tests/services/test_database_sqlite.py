"""Tests against a real SQLite database rather than a mocked Session."""

import asyncio
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import StatementError

from app.db.database import Database
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.utils.clock import LOCAL_TIMEZONE


@pytest.fixture
def database(tmp_path):
    database = Database(url=f"sqlite:///{tmp_path / 'test.db'}")
    database.init()
    return database


@pytest.fixture
def zurich_system_timezone(monkeypatch):
    """Make naive datetime.now() mean Zurich time, as on the Pi."""
    monkeypatch.setenv("TZ", "Europe/Zurich")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _snapshot(timestamp: datetime) -> SensorSnapshot:
    return SensorSnapshot(
        temperature=21.0,
        humidity=40.0,
        light=100.0,
        moisture=0.5,
        pressure=1005.0,
        timestamp=timestamp,
    )


def test_snapshot_timestamps_round_trip_as_aware_utc(database) -> None:
    # Arrange
    zurich_time = datetime(2026, 4, 9, 14, 30, tzinfo=LOCAL_TIMEZONE)

    # Act
    asyncio.run(database.save_snapshot(_snapshot(zurich_time)))
    [stored] = asyncio.run(
        database.get_snapshots_between(
            start_time=zurich_time - timedelta(hours=1),
            end_time=zurich_time + timedelta(hours=1),
        )
    )

    # Assert
    assert stored.timestamp == zurich_time
    assert stored.timestamp.tzinfo == timezone.utc
    assert stored.timestamp.hour == 12


def test_saving_naive_datetime_is_rejected(database) -> None:
    with pytest.raises(StatementError, match="Naive datetime"):
        asyncio.run(
            database.save_snapshot(_snapshot(datetime(2026, 4, 9, 14, 30)))
        )


def test_get_snapshots_between_compares_instants_not_wall_clock(
    database,
) -> None:
    # Arrange: 12:30 UTC is 14:30 in Zurich
    asyncio.run(
        database.save_snapshot(
            _snapshot(datetime(2026, 4, 9, 12, 30, tzinfo=timezone.utc))
        )
    )

    # Act
    in_range = asyncio.run(
        database.get_snapshots_between(
            start_time=datetime(2026, 4, 9, 14, 0, tzinfo=LOCAL_TIMEZONE),
            end_time=datetime(2026, 4, 9, 15, 0, tzinfo=LOCAL_TIMEZONE),
        )
    )
    out_of_range = asyncio.run(
        database.get_snapshots_between(
            start_time=datetime(2026, 4, 9, 12, 0, tzinfo=LOCAL_TIMEZONE),
            end_time=datetime(2026, 4, 9, 13, 0, tzinfo=LOCAL_TIMEZONE),
        )
    )

    # Assert
    assert len(in_range) == 1
    assert out_of_range == []


def test_get_latest_generated_image_returns_newest(database) -> None:
    # Arrange
    for hour in (6, 10):
        asyncio.run(
            database.save_generated_image_metadata(
                filename=f"image_{hour}.jpg",
                prompt="A prompt",
                generated_at=datetime(2026, 4, 9, hour, tzinfo=timezone.utc),
                snapshot=_snapshot(datetime(2026, 4, 9, tzinfo=timezone.utc)),
            )
        )

    # Act
    latest = asyncio.run(database.get_latest_generated_image_metadata())

    # Assert
    assert latest.filename == "image_10.jpg"
    assert latest.generated_at == datetime(2026, 4, 9, 10, tzinfo=timezone.utc)


def test_init_converts_legacy_local_generated_at_to_utc_once(
    tmp_path, zurich_system_timezone
) -> None:
    # Arrange: a pre-migration database with a local-time generated_at
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    legacy = Database(url=url)
    legacy.init()
    with legacy.engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA user_version = 0")
        connection.exec_driver_sql(
            "INSERT INTO generatedimageentity (filename, generated_at, "
            "snapshot_timestamp, temperature, humidity, light, moisture, "
            "pressure) VALUES ('old.jpg', '2026-04-21 00:15:20.013769', "
            "'2026-04-20 22:14:56.598295', 21, 40, 100, 0.5, 1005)"
        )

    # Act: running init twice must only convert once
    Database(url=url).init()
    database = Database(url=url)
    database.init()
    latest = asyncio.run(database.get_latest_generated_image_metadata())

    # Assert: 00:15 in Zurich (CEST) is 22:15 UTC the previous day
    assert latest.generated_at == datetime(
        2026, 4, 20, 22, 15, 20, 13769, tzinfo=timezone.utc
    )
    assert latest.sensor_snapshot.timestamp == datetime(
        2026, 4, 20, 22, 14, 56, 598295, tzinfo=timezone.utc
    )
