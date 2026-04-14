from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from fastapi.params import Depends

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.db.database import Database


class CalculationError(Exception):
    pass


class TimeGroup(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"


class AnalyticsService:
    def __init__(self, database=Depends(Database)):
        self.database = database

    async def get_last_week_snapshots(
            self, group_by: TimeGroup) -> list[SensorSnapshot]:
        snapshots = await self.database.get_snapshots_between(
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now(),
        )
        snapshots_by_hour = defaultdict(list)

        deltas = {
            TimeGroup.HOUR: timedelta(hours=1),
            TimeGroup.DAY: timedelta(days=1),
            TimeGroup.WEEK: timedelta(weeks=1),
        }

        for snapshot in snapshots:
            date_group = self.round_down(
                snapshot.timestamp, deltas[group_by])
            snapshots_by_hour[date_group].append(snapshot)
        averaged_snapshots = []
        for date_group, snapshot in snapshots_by_hour.items():
            avg_snapshot = SensorSnapshot(
                temperature=sum(
                    s.temperature for s in snapshot) / len(snapshot),
                humidity=sum(s.humidity for s in snapshot) / len(snapshot),
                light=sum(s.light for s in snapshot) / len(snapshot),
                moisture=sum(s.moisture for s in snapshot) / len(snapshot),
                pressure=sum(s.pressure for s in snapshot) / len(snapshot),
                timestamp=date_group,
            )
            averaged_snapshots.append(avg_snapshot)
        return averaged_snapshots

    def round_down(self, dt: datetime, delta: timedelta) -> datetime:
        """Round down a datetime to the nearest multiple of a timedelta."""
        seconds = (dt - datetime.min).total_seconds()
        rounded_seconds = seconds - (seconds % delta.total_seconds())
        return datetime.min + timedelta(seconds=rounded_seconds)

    async def get_last_week_average(self) -> SensorSnapshot:
        readings = await self.database.get_snapshots_between(
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now(),
        )

        if not readings:
            raise CalculationError(
                "No sensor readings found for the past week."
            )

        total_readings = len(readings)

        return SensorSnapshot(
            temperature=sum(reading.temperature for reading in readings)
            / total_readings,
            humidity=sum(reading.humidity for reading in readings)
            / total_readings,
            light=sum(reading.light for reading in readings) / total_readings,
            moisture=sum(reading.moisture for reading in readings)
            / total_readings,
            pressure=sum(reading.pressure for reading in readings)
            / total_readings,
        )
