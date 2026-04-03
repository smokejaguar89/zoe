from datetime import datetime, timedelta

from fastapi.params import Depends

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.database import Database


class CalculationError(Exception):
    pass


class AnalyticsService:
    def __init__(self, database=Depends(Database)):
        self.database = database

    async def get_last_week_snapshots(self) -> list[SensorSnapshot]:
        return await self.database.get_snapshots_between(
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now()
        )

    async def get_last_week_average(self) -> SensorSnapshot:
        readings = await self.database.get_snapshots_between(
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now()
        )

        if not readings:
            raise CalculationError(
                "No sensor readings found for the past week.")

        total_readings = len(readings)

        return SensorSnapshot(
            temperature=sum(
                reading.temperature for reading in readings) / total_readings,
            humidity=sum(reading.humidity for reading in readings) /
            total_readings,
            light=sum(reading.light for reading in readings) / total_readings,
            moisture=sum(reading.moisture for reading in readings) /
            total_readings,
            pressure=sum(reading.pressure for reading in readings) /
            total_readings
        )
