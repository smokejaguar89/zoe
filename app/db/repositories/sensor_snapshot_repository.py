from datetime import datetime
import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.models.db.sensor_snapshot_entity import SensorSnapshotEntity
from app.models.domain.sensor_snapshot import SensorSnapshot

logger = logging.getLogger(__name__)


class SensorSnapshotRepository:
    """Reads and writes sensor snapshots. Only services should use this."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def add(self, snapshot: SensorSnapshot) -> None:
        logger.info("Saving sensor data: %s", snapshot)
        with Session(self.engine) as session:
            session.add(SensorSnapshotEntity.from_sensor_snapshot(snapshot))
            session.commit()

    def list_between(
        self, start_time: datetime, end_time: datetime
    ) -> list[SensorSnapshot]:
        """Snapshots in [start_time, end_time], oldest first."""
        with Session(self.engine) as session:
            statement = (
                select(SensorSnapshotEntity)
                .where(SensorSnapshotEntity.timestamp >= start_time)
                .where(SensorSnapshotEntity.timestamp <= end_time)
                .order_by(SensorSnapshotEntity.timestamp)
            )
            return [
                entity.to_sensor_snapshot()
                for entity in session.exec(statement).all()
            ]
