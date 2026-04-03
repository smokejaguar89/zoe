from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.db.generated_image_entity import GeneratedImageEntity
from app.models.db.sensor_snapshot_entity import SensorSnapshotEntity
from app.models.domain.generated_image import GeneratedImage
from app.models.domain.sensor_snapshot import SensorSnapshot


class Database:
    def __init__(self):
        self.SQLITE_URL = "sqlite:///./sensors.db"
        self.engine = create_engine(self.SQLITE_URL)

    def init(self):
        SQLModel.metadata.create_all(self.engine)

    async def save_snapshot(self, snapshot: SensorSnapshot):
        with Session(self.engine) as session:
            print(f"Saving sensor data: {snapshot}")
            session.add(SensorSnapshotEntity.from_sensor_snapshot(snapshot))
            session.commit()

    async def save_generated_image(
            self,
            filename: str,
            generated_at: datetime,
            snapshot: SensorSnapshot):
        with Session(self.engine) as session:
            session.add(
                GeneratedImageEntity.from_generated_image(
                    filename=filename,
                    generated_at=generated_at,
                    snapshot=snapshot,
                )
            )
            session.commit()

    async def get_latest_generated_image(self) -> GeneratedImage | None:
        with Session(self.engine) as session:
            statement = (
                select(GeneratedImageEntity)
                .order_by(GeneratedImageEntity.generated_at.desc())
            )
            result = session.exec(statement).first()
            if result is None:
                return None

            return result.to_generated_image()

    async def get_snapshots_between(
            self,
            start_time: datetime,
            end_time: datetime) -> list[SensorSnapshot]:
        with Session(self.engine) as session:
            statement = (
                select(SensorSnapshotEntity)
                .where(SensorSnapshotEntity.timestamp >= start_time)
                .where(SensorSnapshotEntity.timestamp <= end_time)
            )
            results = session.exec(statement).all()
            return [result.to_sensor_snapshot() for result in results]
