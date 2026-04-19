from dataclasses import dataclass
from datetime import datetime

from app.models.domain.sensor_snapshot import SensorSnapshot


@dataclass
class GeneratedImageMetadata:
    filename: str
    generated_at: datetime
    prompt: str | None = None
    sensor_snapshot: SensorSnapshot | None = None
