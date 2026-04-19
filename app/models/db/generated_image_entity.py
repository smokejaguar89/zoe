import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.domain.generated_image import GeneratedImageMetadata
from app.models.domain.sensor_snapshot import SensorSnapshot


class GeneratedImageEntity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    prompt: Optional[str] = None
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

    def to_generated_image_metadata(self) -> GeneratedImageMetadata:
        return GeneratedImageMetadata(
            filename=self.filename,
            generated_at=self.generated_at,
            prompt=self.prompt,
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
    def from_generated_image_metadata(
        cls,
        metadata: GeneratedImageMetadata,
    ) -> "GeneratedImageEntity":
        return cls(
            filename=metadata.filename,
            prompt=metadata.prompt,
            generated_at=metadata.generated_at,
            snapshot_timestamp=metadata.sensor_snapshot.timestamp,
            temperature=metadata.sensor_snapshot.temperature,
            humidity=metadata.sensor_snapshot.humidity,
            light=metadata.sensor_snapshot.light,
            moisture=metadata.sensor_snapshot.moisture,
            pressure=metadata.sensor_snapshot.pressure,
        )
