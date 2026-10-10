from datetime import datetime, time, timedelta, timezone
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.database import Database
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService
from app.utils.clock import LOCAL_TIMEZONE, to_local, utc_now

logger = logging.getLogger(__name__)
RETRY_DELAY_MINUTES = 5
# Per scheduled slot, including the first try. Each attempt can make up to
# GeminiClient's MAX_ATTEMPTS calls.
MAX_IMAGE_GENERATION_ATTEMPTS = 3
MISFIRE_GRACE_SECONDS = 5 * 60
RETRY_JOB_ID = "generate_image_retry"
IMAGE_GEN_CRON_SCHEDULE = [
    6,  # Clara awake
    10,  # Nick prooooobably awake
    14,  # Lunch time
    18,  # Evening, hopefully home (or out, living life)
    22,  # Night time, maybe one last image before bed
]
# Give the generation job time to finish before the display pulls
PULL_BUFFER_MINUTES = 10


def get_next_image_pull_time(now: Optional[datetime] = None) -> datetime:
    """Return the next time (UTC) a freshly generated image will be ready."""
    now = to_local(now or utc_now())
    for day_offset in (0, 1):
        day = now.date() + timedelta(days=day_offset)
        for hour in IMAGE_GEN_CRON_SCHEDULE:
            # Build each slot as local wall-clock time so DST is respected
            candidate = datetime.combine(
                day, time(hour), tzinfo=LOCAL_TIMEZONE
            ) + timedelta(minutes=PULL_BUFFER_MINUTES)
            if candidate > now + timedelta(minutes=1):
                return candidate.astimezone(timezone.utc)
    raise RuntimeError("IMAGE_GEN_CRON_SCHEDULE is empty.")


class Scheduler:
    def __init__(
        self,
        sensor_service: SensorService,
        database: Database,
        image_generation_service: ImageGenerationService,
        scheduler: Optional[AsyncIOScheduler] = None,
    ):
        self.sensor_service = sensor_service
        self.database = database
        self.image_generation_service = image_generation_service
        # Jobs run on the app's event loop, alongside API requests, so every
        # hardware read happens on one loop and the drivers' asyncio locks
        # actually serialise access. The timezone is explicit so cron hours
        # are Zurich time whatever the Pi's system timezone is set to.
        self._scheduler = scheduler or AsyncIOScheduler(
            timezone=LOCAL_TIMEZONE,
            # Run a job that's slightly late (e.g. the loop was busy)
            # rather than skipping it after APScheduler's default 1s
            job_defaults={"misfire_grace_time": MISFIRE_GRACE_SECONDS},
        )

    async def _collect_data_job(self):
        logger.info("Running data collection job...")
        snapshot = await self.sensor_service.get_snapshot()
        await self.database.save_snapshot(snapshot)

    async def _generate_image_job(self, attempt: int = 1):
        logger.info(
            "Running image generation job (attempt %d/%d)...",
            attempt,
            MAX_IMAGE_GENERATION_ATTEMPTS,
        )
        try:
            await self.image_generation_service.generate_and_save_image()
        except Exception:
            if attempt >= MAX_IMAGE_GENERATION_ATTEMPTS:
                logger.exception(
                    "Image generation failed after %d attempts. Giving up "
                    "until the next scheduled slot.",
                    attempt,
                )
                return
            logger.exception(
                "Image generation failed. Retrying in %d minutes.",
                RETRY_DELAY_MINUTES,
            )
            self._schedule_generate_image_retry(attempt + 1)

    def _schedule_generate_image_retry(self, attempt: int):
        self._scheduler.add_job(
            self._generate_image_job,
            "date",
            run_date=utc_now() + timedelta(minutes=RETRY_DELAY_MINUTES),
            kwargs={"attempt": attempt},
            id=RETRY_JOB_ID,
            replace_existing=True,
        )

    def start(self):
        """Start the scheduler. Must be called from the running event loop."""
        self._scheduler.add_job(self._collect_data_job, "interval", minutes=15)
        # For testing
        # self._scheduler.add_job(self._generate_image_job, "interval",
        #                         minutes=1)

        self._scheduler.add_job(
            self._generate_image_job,
            "cron",
            hour=",".join(map(str, IMAGE_GEN_CRON_SCHEDULE)),
            minute=0,
        )
        self._scheduler.start()

    def stop(self):
        self._scheduler.shutdown(wait=False)
