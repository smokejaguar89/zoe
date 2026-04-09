import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import Database
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService

scheduler = BackgroundScheduler()
logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
            self,
            sensor_service: SensorService,
            database: Database,
            image_generation_service: ImageGenerationService):
        self.sensor_service = sensor_service
        self.database = database
        self.image_generation_service = image_generation_service

    async def _collect_data_job(self):
        logger.info("Running data collection job...")
        snapshot = await self.sensor_service.get_snapshot()
        await self.database.save_snapshot(snapshot)

    def _run_collect_data_job(self):
        asyncio.run(self._collect_data_job())

    async def _generate_image_job(self):
        logger.info("Running image generation job...")
        await self.image_generation_service.generate_and_save_image()

    def _run_generate_image_job(self):
        asyncio.run(self._generate_image_job())

    def start(self):
        scheduler.add_job(
            self._run_collect_data_job,
            'interval',
            minutes=15
        )
        scheduler.add_job(
            self._run_generate_image_job,
            'interval',
            hours=6
        )
        scheduler.start()

    def stop(self):
        scheduler.shutdown()
