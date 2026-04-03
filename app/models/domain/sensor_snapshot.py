from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SensorSnapshot:
    light: float
    temperature: float
    humidity: float
    moisture: float
    pressure: float
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
