import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect

from app.db.database import Database
from app.db.repositories.generated_image_repository import (
    GeneratedImageRepository,
)


@pytest.fixture
def zurich_system_timezone(monkeypatch):
    """Make naive datetime.now() mean Zurich time, as on the Pi."""
    monkeypatch.setenv("TZ", "Europe/Zurich")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_init_creates_database_tables(database) -> None:
    assert {"sensorsnapshotentity", "generatedimageentity"} <= set(
        inspect(database.engine).get_table_names()
    )


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
    latest = GeneratedImageRepository(engine=database.engine).get_latest()

    # Assert: 00:15 in Zurich (CEST) is 22:15 UTC the previous day
    assert latest.generated_at == datetime(
        2026, 4, 20, 22, 15, 20, 13769, tzinfo=timezone.utc
    )
    assert latest.sensor_snapshot.timestamp == datetime(
        2026, 4, 20, 22, 14, 56, 598295, tzinfo=timezone.utc
    )
