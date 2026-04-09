from functools import lru_cache

from app.clients.gemini_client import GeminiClient
from app.db.database import Database
from app.hardware.bme280_driver import BME280Driver
from app.hardware.sparkfun_driver import SparkfunDriver
from app.hardware.tsl2591_driver import TSL2591Driver
from app.scheduler.scheduler import Scheduler
from app.services.analytics_service import AnalyticsService
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService


@lru_cache
def get_database() -> Database:
    return Database()


@lru_cache
def get_bme280_driver() -> BME280Driver:
    return BME280Driver()


@lru_cache
def get_tsl2591_driver() -> TSL2591Driver:
    return TSL2591Driver()


@lru_cache
def get_sparkfun_driver() -> SparkfunDriver:
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
