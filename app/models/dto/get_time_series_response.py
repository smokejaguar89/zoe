from pydantic import BaseModel, ConfigDict


class SensorSnapshotDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    temperature: float
    humidity: float
    light: float
    moisture: float
    pressure: float
    timestamp: str  # ISO format string for easier JSON serialization


class GetTimeSeriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshots: list[SensorSnapshotDto]
