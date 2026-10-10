from datetime import datetime, timezone
import logging

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.db.generated_image_entity import GeneratedImageEntity
from app.models.db.sensor_snapshot_entity import SensorSnapshotEntity
from app.models.domain.generated_image import GeneratedImageMetadata
from app.models.domain.sensor_snapshot import SensorSnapshot

logger = logging.getLogger(__name__)

SQLITE_URL = "sqlite:///./sensors.db"
# Bump when adding a migration to _run_migrations
SCHEMA_VERSION = 1
# Format SQLAlchemy uses to store datetimes in SQLite
_SQLITE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class EntityNotFoundError(Exception):
    pass


class Database:
    def __init__(self, url: str = SQLITE_URL):
        self.engine = create_engine(url)

    def init(self):
        SQLModel.metadata.create_all(self.engine)
        self._ensure_generated_image_prompt_column()
        self._run_migrations()

    def _run_migrations(self):
        with self.engine.begin() as connection:
            version = connection.exec_driver_sql(
                "PRAGMA user_version"
            ).scalar()
            if version >= SCHEMA_VERSION:
                return
            if version < 1:
                self._convert_generated_at_to_utc(connection)
            connection.exec_driver_sql(
                f"PRAGMA user_version = {SCHEMA_VERSION}"
            )

    def _convert_generated_at_to_utc(self, connection):
        # generated_at used to be written with naive datetime.now(), i.e. the
        # system's local time. Sensor timestamps were already UTC.
        rows = connection.exec_driver_sql(
            "SELECT id, generated_at FROM generatedimageentity"
        ).fetchall()
        for row_id, generated_at in rows:
            # astimezone() on a naive datetime assumes system local time
            utc = (
                datetime.fromisoformat(generated_at)
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )
            connection.exec_driver_sql(
                "UPDATE generatedimageentity "
                "SET generated_at = ? WHERE id = ?",
                (utc.strftime(_SQLITE_DATETIME_FORMAT), row_id),
            )
        logger.info("Converted %d generated_at values to UTC.", len(rows))

    def _ensure_generated_image_prompt_column(self):
        with self.engine.begin() as connection:
            columns = connection.exec_driver_sql(
                "PRAGMA table_info(generatedimageentity)"
            ).fetchall()
            column_names = {column[1] for column in columns}
            if "prompt" not in column_names:
                connection.execute(
                    text(
                        "ALTER TABLE generatedimageentity "
                        "ADD COLUMN prompt TEXT"
                    )
                )

    async def save_snapshot(self, snapshot: SensorSnapshot):
        with Session(self.engine) as session:
            logger.info(f"Saving sensor data: {snapshot}")
            session.add(SensorSnapshotEntity.from_sensor_snapshot(snapshot))
            session.commit()

    async def save_generated_image_metadata(
        self,
        filename: str,
        prompt: str,
        generated_at: datetime,
        snapshot: SensorSnapshot,
    ):
        metadata = GeneratedImageMetadata(
            filename=filename,
            prompt=prompt,
            generated_at=generated_at,
            sensor_snapshot=snapshot,
        )
        with Session(self.engine) as session:
            session.add(
                GeneratedImageEntity.from_generated_image_metadata(metadata)
            )
            session.commit()

    async def get_latest_generated_image_metadata(
        self,
    ) -> GeneratedImageMetadata:

        with Session(self.engine) as session:
            statement = select(GeneratedImageEntity).order_by(
                GeneratedImageEntity.generated_at.desc()
            )
            result = session.exec(statement).first()
            if result is None:
                raise EntityNotFoundError("No generated image found.")

            return result.to_generated_image_metadata()

    async def get_snapshots_between(
        self, start_time: datetime, end_time: datetime
    ) -> list[SensorSnapshot]:
        with Session(self.engine) as session:
            statement = (
                select(SensorSnapshotEntity)
                .where(SensorSnapshotEntity.timestamp >= start_time)
                .where(SensorSnapshotEntity.timestamp <= end_time)
            )
            results = session.exec(statement).all()
            return [result.to_sensor_snapshot() for result in results]
