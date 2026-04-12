from __future__ import annotations

import os
from functools import lru_cache

from app.clients.gemini_client import GeminiClient
from app.clients.news_api_client import NewsApiClient
from app.clients.open_meteo_client import OpenMeteoClient
from app.db.database import Database
from app.hardware.fake_drivers import (
    FakeBME280Driver,
    FakeLockedI2CBus,
    FakeSoilMoistureDriver,
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


if is_test_mode():
    LockedI2CBus = FakeLockedI2CBus
    BME280Driver = FakeBME280Driver
    TSL2591Driver = FakeTSL2591Driver
    SoilMoistureDriver = FakeSoilMoistureDriver
else:
    from app.hardware.bme280_driver import BME280Driver
    from app.hardware.locked_i2c_bus import LockedI2CBus
    from app.hardware.soil_moisture_driver import SoilMoistureDriver
    from app.hardware.tsl2591_driver import TSL2591Driver


@lru_cache
def get_database() -> Database:
    return Database()


@lru_cache
def get_i2c_bus():
    # This is the important shared singleton for I2C-based sensors.
    # Multiple driver instances are fine as long as they all use this
    # same bus wrapper, because it owns the shared lock.
    return LockedI2CBus()


# I2C drivers are plain factories: they do not need to be singletons now
# that concurrency safety is enforced by the shared LockedI2CBus.
def get_bme280_driver():
    return BME280Driver(i2c_bus=get_i2c_bus())


def get_tsl2591_driver():
    return TSL2591Driver(i2c_bus=get_i2c_bus())


@lru_cache
def get_soil_moisture_driver():
    # Soil moisture driver remains singleton-scoped because correctness
    # depends on coordinating shared GPIO power state in one instance.
    return SoilMoistureDriver()


def get_sparkfun_driver():
    # Backward-compatible alias.
    return get_soil_moisture_driver()


def get_sensor_service() -> SensorService:
    return SensorService(
        bme280=get_bme280_driver(),
        tsl2591=get_tsl2591_driver(),
        soil_moisture=get_soil_moisture_driver(),
    )


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


def get_news_api_client() -> NewsApiClient:
    return NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))


def get_open_meteo_client() -> OpenMeteoClient:
    return OpenMeteoClient()


def get_image_generation_service() -> ImageGenerationService:
    return ImageGenerationService(
        sensor_service=get_sensor_service(),
        image_client=get_gemini_client(),
        database=get_database(),
        news_api_client=get_news_api_client(),
        open_meteo_client=get_open_meteo_client(),
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
