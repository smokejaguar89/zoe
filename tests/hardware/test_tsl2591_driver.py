import asyncio
from unittest.mock import MagicMock, patch

from app.hardware.i2c_bus import I2CBus
from app.hardware.tsl2591_driver import TSL2591Driver
from app.models.domain.tsl2591_reading import TSL2591Reading


@patch("app.hardware.tsl2591_driver.adafruit_tsl2591.TSL2591")
def test_initialises_sensor_on_shared_bus(sensor_cls) -> None:
    # Arrange
    raw_bus = object()
    bus = I2CBus(bus=raw_bus)

    # Act
    TSL2591Driver(bus=bus)

    # Assert
    sensor_cls.assert_called_once_with(raw_bus)
    bus.shutdown()


@patch("app.hardware.tsl2591_driver.adafruit_tsl2591.TSL2591")
def test_get_reading_maps_sensor_values(sensor_cls) -> None:
    # Arrange
    sensor_cls.return_value = MagicMock(lux=24.3)
    bus = I2CBus(bus=object())
    driver = TSL2591Driver(bus=bus)

    # Act
    reading = asyncio.run(driver.get_reading())

    # Assert
    assert reading == TSL2591Reading(luminous_flux=24.3)
    bus.shutdown()
