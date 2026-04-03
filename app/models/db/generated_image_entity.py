import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.domain.generated_image import GeneratedImage
from app.models.domain.sensor_snapshot import SensorSnapshot


class GeneratedImageEntity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    generated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True,
    )
    snapshot_timestamp: datetime.datetime
    temperature: float
    humidity: float
    light: float
    moisture: float
    pressure: float

    def to_generated_image(self) -> GeneratedImage:
        return GeneratedImage(
            filename=self.filename,
            generated_at=self.generated_at,
            sensor_snapshot=SensorSnapshot(
                light=self.light,
                temperature=self.temperature,
                humidity=self.humidity,
                moisture=self.moisture,
                pressure=self.pressure,
                timestamp=self.snapshot_timestamp,
            ),
        )

    @classmethod
    def from_generated_image(
            cls,
            filename: str,
            generated_at: datetime.datetime,
            snapshot: SensorSnapshot) -> "GeneratedImageEntity":
        return cls(
            filename=filename,
            generated_at=generated_at,
            snapshot_timestamp=snapshot.timestamp,
            temperature=snapshot.temperature,
            humidity=snapshot.humidity,
            light=snapshot.light,
            moisture=snapshot.moisture,
            pressure=snapshot.pressure,
        )
