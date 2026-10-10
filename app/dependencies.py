from __future__ import annotations

import os
from functools import lru_cache

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.clients.gemini_client import GeminiClient
from app.clients.news_api_client import NewsApiClient
from app.clients.open_meteo_client import OpenMeteoClient
from app.db.database import Database
from app.db.repositories.generated_image_repository import (
    GeneratedImageRepository,
)
from app.db.repositories.sensor_snapshot_repository import (
    SensorSnapshotRepository,
)
from app.hardware.driver_protocols import HardwareDriverProtocol
from app.hardware.fake_drivers import (
    FakeBME280Driver,
    FakeSoilMoistureDriver,
    FakeTSL2591Driver,
)
from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.soil_moisture_reading import SoilMoistureReading
from app.models.domain.tsl2591_reading import TSL2591Reading
from app.scheduler.scheduler import MISFIRE_GRACE_SECONDS, Scheduler
from app.services.analytics_service import AnalyticsService
from app.services.generated_image_service import GeneratedImageService
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService
from app.utils.clock import LOCAL_TIMEZONE
from app.utils.env import is_test_mode
from app.utils.prompt_builder import ImagePromptBuilder

# The real drivers need hardware libraries (board, adafruit_*, gpiozero)
# that only exist on the Pi, so they're only imported outside test mode.
TEST_MODE = is_test_mode()
if not TEST_MODE:
    from app.hardware.bme280_driver import BME280Driver
    from app.hardware.i2c_bus import I2CBus
    from app.hardware.soil_moisture_driver import SoilMoistureDriver
    from app.hardware.tsl2591_driver import TSL2591Driver


@lru_cache
def get_database() -> Database:
    return Database()


def get_sensor_snapshot_repository() -> SensorSnapshotRepository:
    return SensorSnapshotRepository(engine=get_database().engine)


def get_generated_image_repository() -> GeneratedImageRepository:
    return GeneratedImageRepository(engine=get_database().engine)


# Drivers are cached so each sensor chip is initialised once and shared.


@lru_cache
def get_i2c_bus() -> I2CBus:
    # One bus for all I2C sensors, so their reads run on a single thread
    return I2CBus()


@lru_cache
def get_bme280_driver() -> HardwareDriverProtocol[BME280Reading]:
    if TEST_MODE:
        return FakeBME280Driver()
    return BME280Driver(bus=get_i2c_bus())


@lru_cache
def get_tsl2591_driver() -> HardwareDriverProtocol[TSL2591Reading]:
    if TEST_MODE:
        return FakeTSL2591Driver()
    return TSL2591Driver(bus=get_i2c_bus())


@lru_cache
def get_soil_moisture_driver() -> HardwareDriverProtocol[SoilMoistureReading]:
    # Must be a single instance: it owns the sensor's GPIO power pin and the
    # lock that stops reads from toggling it over each other
    if TEST_MODE:
        return FakeSoilMoistureDriver()
    return SoilMoistureDriver()


def get_sensor_service() -> SensorService:
    return SensorService(
        bme280=get_bme280_driver(),
        tsl2591=get_tsl2591_driver(),
        soil_moisture=get_soil_moisture_driver(),
        snapshot_repository=get_sensor_snapshot_repository(),
    )


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


def get_news_api_client() -> NewsApiClient:
    return NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))


def get_open_meteo_client() -> OpenMeteoClient:
    return OpenMeteoClient()


def get_prompt_builder() -> ImagePromptBuilder:
    return ImagePromptBuilder()


def get_image_generation_service() -> ImageGenerationService:
    return ImageGenerationService(
        sensor_service=get_sensor_service(),
        image_client=get_gemini_client(),
        image_repository=get_generated_image_repository(),
        news_api_client=get_news_api_client(),
        open_meteo_client=get_open_meteo_client(),
        prompt_builder=get_prompt_builder(),
    )


def get_generated_image_service() -> GeneratedImageService:
    return GeneratedImageService(
        image_repository=get_generated_image_repository()
    )


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(
        snapshot_repository=get_sensor_snapshot_repository()
    )


def get_apscheduler() -> AsyncIOScheduler:
    return AsyncIOScheduler(
        # Explicit so cron hours are Zurich time whatever the Pi's system
        # timezone is set to
        timezone=LOCAL_TIMEZONE,
        # Run a job that's slightly late (e.g. the loop was busy) rather
        # than skipping it after APScheduler's default 1s
        job_defaults={"misfire_grace_time": MISFIRE_GRACE_SECONDS},
    )


@lru_cache
def get_scheduler() -> Scheduler:
    return Scheduler(
        sensor_service=get_sensor_service(),
        image_generation_service=get_image_generation_service(),
        scheduler=get_apscheduler(),
    )
