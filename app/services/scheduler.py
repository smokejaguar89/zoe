import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.database import Database
from app.services.sensor_service import SensorService

scheduler = BackgroundScheduler()


class Scheduler:

    def __init__(self, sensor_service: SensorService, database: Database):
        self.sensor_service = sensor_service
        self.database = database

    async def _collect_data_job(self):
        """Note: We now accept the service as an argument"""
        snapshot = await self.sensor_service.get_snapshot()
        await self.database.save_snapshot(snapshot)

    def _run_collect_data_job(self):
        asyncio.run(self._collect_data_job())

    def start(self):
        # Use 'args' to inject the service into the job
        scheduler.add_job(
            self._run_collect_data_job,
            'interval',
            minutes=1
        )
        scheduler.start()

    def stop(self):
        scheduler.shutdown()
