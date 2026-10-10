from datetime import datetime

from app.models.domain.sensor_snapshot import SensorSnapshot


def make_snapshot(timestamp: datetime) -> SensorSnapshot:
    return SensorSnapshot(
        temperature=21.0,
        humidity=40.0,
        light=100.0,
        moisture=0.5,
        pressure=1005.0,
        timestamp=timestamp,
    )
