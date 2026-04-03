import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.db.database import Database
from app.models.db.generated_image_entity import GeneratedImageEntity


@patch("app.db.database.SQLModel.metadata.create_all")
def test_init_creates_database_tables(create_all) -> None:
    db = Database()

    db.init()

    create_all.assert_called_once_with(db.engine)


@patch("app.db.database.Session")
def test_save_sensor_data_adds_and_commits_reading(session_cls) -> None:
    db = Database()
    snapshot = SensorSnapshot(
        temperature=24.2,
        humidity=46.5,
        light=320.0,
        moisture=19.0,
        pressure=1007.2,
    )
    session = MagicMock()
    session_cls.return_value.__enter__.return_value = session

    asyncio.run(db.save_snapshot(snapshot))

    session_cls.assert_called_once_with(db.engine)
    session.add.assert_called_once()
    session.commit.assert_called_once()


@patch("app.db.database.Session")
def test_save_generated_image_adds_and_commits_record(session_cls) -> None:
    db = Database()
    snapshot = SensorSnapshot(
        temperature=24.2,
        humidity=46.5,
        light=320.0,
        moisture=19.0,
        pressure=1007.2,
    )
    session = MagicMock()
    session_cls.return_value.__enter__.return_value = session

    asyncio.run(
        db.save_generated_image(
            filename="sunflower_2026-04-03:13:39.jpg",
            generated_at=datetime(2026, 4, 3, 13, 39),
            snapshot=snapshot,
        )
    )

    session_cls.assert_called_once_with(db.engine)
    session.add.assert_called_once()
    session.commit.assert_called_once()


@patch("app.db.database.Session")
def test_get_latest_generated_image_returns_record(session_cls) -> None:
    db = Database()
    entity = GeneratedImageEntity(
        filename="sunflower_2026-04-03:13:39.jpg",
        generated_at=datetime(2026, 4, 3, 13, 39),
        snapshot_timestamp=datetime(2026, 4, 3, 13, 38),
        temperature=24.2,
        humidity=46.5,
        light=320.0,
        moisture=19.0,
        pressure=1007.2,
    )
    session = MagicMock()
    session.exec.return_value.first.return_value = entity
    session_cls.return_value.__enter__.return_value = session

    generated_image = asyncio.run(db.get_latest_generated_image())

    assert generated_image is not None
    assert generated_image.filename == "sunflower_2026-04-03:13:39.jpg"
    assert generated_image.sensor_snapshot is not None
    assert generated_image.sensor_snapshot.moisture == 19.0
