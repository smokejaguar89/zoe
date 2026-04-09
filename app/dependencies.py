import os
from functools import lru_cache

from app.clients.gemini_client import GeminiClient
from app.db.database import Database
from app.hardware.fake_drivers import (
    FakeBME280Driver,
    FakeSparkfunDriver,
    FakeTSL2591Driver,
)
from app.scheduler.scheduler import Scheduler
from app.services.analytics_service import AnalyticsService
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService


def is_test_mode() -> bool:
    sensor_mode = os.getenv("SENSOR_MODE", "").strip().upper()
    if sensor_mode == "TEST":
        return True

    test_flag = os.getenv("TEST", "").strip().lower()
    return test_flag in {"1", "true", "yes", "on"}


@lru_cache
def get_database() -> Database:
    return Database()


@lru_cache
def get_bme280_driver():
    if is_test_mode():
        return FakeBME280Driver()

    from app.hardware.bme280_driver import BME280Driver

    return BME280Driver()


@lru_cache
def get_tsl2591_driver():
    if is_test_mode():
        return FakeTSL2591Driver()

    from app.hardware.tsl2591_driver import TSL2591Driver

    return TSL2591Driver()


@lru_cache
def get_sparkfun_driver():
    if is_test_mode():
        return FakeSparkfunDriver()

    from app.hardware.sparkfun_driver import SparkfunDriver

    return SparkfunDriver()


def get_sensor_service() -> SensorService:
    return SensorService(
        bme280=get_bme280_driver(),
        tsl2591=get_tsl2591_driver(),
        sparkfun=get_sparkfun_driver(),
    )


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


def get_image_generation_service() -> ImageGenerationService:
    return ImageGenerationService(
        sensor_service=get_sensor_service(),
        image_client=get_gemini_client(),
        database=get_database(),
    )


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(database=get_database())


@lru_cache
def get_scheduler() -> Scheduler:
    return Scheduler(
        sensor_service=get_sensor_service(),
        database=get_database(),
        image_generation_service=get_image_generation_service(),
    )
