from datetime import datetime
import logging

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.db.generated_image_entity import GeneratedImageEntity
from app.models.db.sensor_snapshot_entity import SensorSnapshotEntity
from app.models.domain.generated_image import GeneratedImageMetadata
from app.models.domain.sensor_snapshot import SensorSnapshot

logger = logging.getLogger(__name__)


class EntityNotFoundError(Exception):
    pass


class Database:
    def __init__(self):
        self.SQLITE_URL = "sqlite:///./sensors.db"
        self.engine = create_engine(self.SQLITE_URL)

    def init(self):
        SQLModel.metadata.create_all(self.engine)
        self._ensure_generated_image_prompt_column()

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
