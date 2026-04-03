import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.domain.sensor_snapshot import SensorSnapshot


class SensorSnapshotEntity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    temperature: float
    humidity: float
    light: float
    moisture: float
    pressure: float
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_sensor_snapshot(self) -> SensorSnapshot:
        return SensorSnapshot(
            light=self.light,
            temperature=self.temperature,
            humidity=self.humidity,
            moisture=self.moisture,
            pressure=self.pressure,
            timestamp=self.timestamp
        )

    @classmethod
    def from_sensor_snapshot(
            cls,
            snapshot: SensorSnapshot) -> "SensorSnapshotEntity":
        """
        Factory method to convert an internal SensorSnapshot object
        into a database-ready SensorSnapshotEntity.
        """
        return cls(
            temperature=snapshot.temperature,
            humidity=snapshot.humidity,
            light=snapshot.light,
            moisture=snapshot.moisture,
            pressure=snapshot.pressure,
            timestamp=snapshot.timestamp
        )
