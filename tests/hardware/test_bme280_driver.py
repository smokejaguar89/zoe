import asyncio
from unittest.mock import MagicMock, patch

from app.hardware.bme280_driver import BME280Driver
from app.hardware.i2c_bus import I2CBus
from app.models.domain.bme280_reading import BME280Reading


@patch("app.hardware.bme280_driver.adafruit_bme280.Adafruit_BME280_I2C")
def test_initialises_sensor_on_shared_bus_at_its_address(sensor_cls) -> None:
    # Arrange
    raw_bus = object()
    bus = I2CBus(bus=raw_bus)

    # Act
    BME280Driver(bus=bus)

    # Assert
    sensor_cls.assert_called_once_with(raw_bus, address=0x76)
    bus.shutdown()


@patch("app.hardware.bme280_driver.adafruit_bme280.Adafruit_BME280_I2C")
def test_get_reading_maps_sensor_values(sensor_cls) -> None:
    # Arrange
    sensor_cls.return_value = MagicMock(
        temperature=21.1, relative_humidity=45.2, pressure=1001.3
    )
    bus = I2CBus(bus=object())
    driver = BME280Driver(bus=bus)

    # Act
    reading = asyncio.run(driver.get_reading())

    # Assert
    assert reading == BME280Reading(
        ambient_temp_celsius=21.1,
        relative_humidity_pct=45.2,
        barometric_pressure_hpa=1001.3,
    )
    bus.shutdown()
