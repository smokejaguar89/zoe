import asyncio
from datetime import datetime, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import Database
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService

scheduler = BackgroundScheduler()
logger = logging.getLogger(__name__)
RETRY_DELAY_MINUTES = 5
RETRY_JOB_ID = "generate_image_retry"


class Scheduler:
    def __init__(
        self,
        sensor_service: SensorService,
        database: Database,
        image_generation_service: ImageGenerationService,
    ):
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
        try:
            asyncio.run(self._generate_image_job())
        except Exception:
            logger.exception(
                "Image generation job failed. Scheduling retry in %d minutes.",
                RETRY_DELAY_MINUTES,
            )
            self._schedule_generate_image_retry()

    def _schedule_generate_image_retry(self):
        retry_at = datetime.now() + timedelta(minutes=RETRY_DELAY_MINUTES)
        scheduler.add_job(
            self._run_generate_image_job,
            "date",
            run_date=retry_at,
            id=RETRY_JOB_ID,
            replace_existing=True,
        )

    def start(self):
        scheduler.add_job(self._run_collect_data_job, "interval", minutes=15)
        # For testing
        # scheduler.add_job(self._run_generate_image_job, "interval", minutes=1)

        IMAGE_GEN_CRON_SCHEDULE = [
            6,  # Clara awake
            10,  # Nick prooooobably awake
            14,  # Lunch time
            18,  # Evening, hopefully home (or out, living life)
            22,  # Night time, maybe one last image before bed
        ]
        scheduler.add_job(
            self._run_generate_image_job,
            "cron",
            hour=",".join(map(str, IMAGE_GEN_CRON_SCHEDULE)),
            minute=0,
        )
        scheduler.start()

    def stop(self):
        scheduler.shutdown()
