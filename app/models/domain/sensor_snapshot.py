from dataclasses import dataclass, field
from datetime import datetime

from app.utils.clock import utc_now


@dataclass
class SensorSnapshot:
    light: float
    temperature: float
    humidity: float
    moisture: float
    pressure: float
    timestamp: datetime = field(default_factory=utc_now)
