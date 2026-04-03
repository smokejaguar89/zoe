import asyncio
from unittest.mock import MagicMock, patch

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.db.database import Database


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
