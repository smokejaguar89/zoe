import asyncio
from unittest.mock import patch, sentinel

import pytest

from app import dependencies
from app.hardware.bme280_driver import BME280Driver
from app.hardware.fake_drivers import (
    FakeBME280Driver,
    FakeSoilMoistureDriver,
    FakeTSL2591Driver,
)
from app.hardware.soil_moisture_driver import SoilMoistureDriver
from app.hardware.tsl2591_driver import TSL2591Driver
from app.scheduler.scheduler import MISFIRE_GRACE_SECONDS
from app.utils.clock import LOCAL_TIMEZONE

_CACHED_HARDWARE_PROVIDERS = (
    dependencies.get_i2c_bus,
    dependencies.get_bme280_driver,
    dependencies.get_tsl2591_driver,
    dependencies.get_soil_moisture_driver,
)


@pytest.fixture(autouse=True)
def clear_provider_caches():
    for provider in _CACHED_HARDWARE_PROVIDERS:
        provider.cache_clear()
    yield
    for provider in _CACHED_HARDWARE_PROVIDERS:
        provider.cache_clear()


@pytest.fixture
def hardware_mode(monkeypatch):
    monkeypatch.delenv("SENSOR_MODE", raising=False)
    monkeypatch.delenv("TEST", raising=False)


def test_dependency_providers_use_fake_drivers_in_test_mode(monkeypatch):
    # Arrange
    monkeypatch.setenv("SENSOR_MODE", "TEST")

    # Act
    bme280 = dependencies.get_bme280_driver()
    tsl2591 = dependencies.get_tsl2591_driver()
    soil_moisture = dependencies.get_soil_moisture_driver()

    # Assert
    assert isinstance(bme280, FakeBME280Driver)
    assert isinstance(tsl2591, FakeTSL2591Driver)
    assert isinstance(soil_moisture, FakeSoilMoistureDriver)


def test_test_mode_does_not_touch_the_i2c_bus(monkeypatch):
    # Arrange
    monkeypatch.setenv("SENSOR_MODE", "TEST")

    # Act
    with patch("app.hardware.i2c_bus.I2CBus") as bus_cls:
        dependencies.get_bme280_driver()
        dependencies.get_tsl2591_driver()

    # Assert
    bus_cls.assert_not_called()


@patch("app.hardware.tsl2591_driver.TSL2591Driver")
@patch("app.hardware.bme280_driver.BME280Driver")
@patch("app.hardware.i2c_bus.I2CBus")
def test_i2c_drivers_share_one_bus(
    bus_cls, bme280_cls, tsl2591_cls, hardware_mode
):
    # Act
    dependencies.get_bme280_driver()
    dependencies.get_tsl2591_driver()

    # Assert
    bus_cls.assert_called_once_with()
    bme280_cls.assert_called_once_with(bus=bus_cls.return_value)
    tsl2591_cls.assert_called_once_with(bus=bus_cls.return_value)


@patch("app.hardware.bme280_driver.BME280Driver")
@patch("app.hardware.i2c_bus.I2CBus")
def test_i2c_drivers_are_initialised_once(bus_cls, bme280_cls, hardware_mode):
    # Act
    first = dependencies.get_bme280_driver()
    second = dependencies.get_bme280_driver()

    # Assert
    assert first is second
    bme280_cls.assert_called_once()


@patch(
    "app.hardware.soil_moisture_driver.SoilMoistureDriver",
    return_value=sentinel.soil_moisture_driver,
)
def test_soil_moisture_driver_provider_is_singleton(
    soil_moisture_cls, hardware_mode
):
    # Act
    first = dependencies.get_soil_moisture_driver()
    second = dependencies.get_soil_moisture_driver()

    # Assert
    assert first is second
    assert first is sentinel.soil_moisture_driver
    soil_moisture_cls.assert_called_once_with()


def test_hardware_mode_sensor_service_reads_real_drivers(hardware_mode):
    """Exercises the Pi's wiring end to end, with the stub chips from
    conftest.py standing in for the Adafruit and gpiozero libraries."""
    # Arrange
    sensor_service = dependencies.get_sensor_service()

    # Act
    snapshot = asyncio.run(sensor_service.get_snapshot())

    # Assert
    assert isinstance(sensor_service.bme280, BME280Driver)
    assert isinstance(sensor_service.tsl2591, TSL2591Driver)
    assert isinstance(sensor_service.soil_moisture, SoilMoistureDriver)
    assert snapshot.temperature == 0.0
    assert snapshot.light == 0.0
    assert snapshot.moisture == 0.0
    dependencies.get_i2c_bus().shutdown()


def test_apscheduler_uses_zurich_time_and_misfire_grace() -> None:
    # Act
    scheduler = dependencies.get_apscheduler()

    # Assert
    assert scheduler.timezone == LOCAL_TIMEZONE
    assert scheduler._job_defaults["misfire_grace_time"] == (
        MISFIRE_GRACE_SECONDS
    )
