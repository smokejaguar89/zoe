from dataclasses import dataclass
from datetime import datetime

from app.models.domain.sensor_snapshot import SensorSnapshot


@dataclass
class GeneratedImage:
    filename: str
    generated_at: datetime
    sensor_snapshot: SensorSnapshot | None = None
