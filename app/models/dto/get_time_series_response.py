from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorSnapshotDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    temperature: float
    humidity: float
    light: float
    moisture: float
    pressure: float
    timestamp: datetime  # Serialized as ISO 8601 with a UTC offset


class GetTimeSeriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshots: list[SensorSnapshotDto]
