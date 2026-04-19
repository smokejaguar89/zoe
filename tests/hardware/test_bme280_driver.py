from unittest.mock import MagicMock, AsyncMock
import asyncio

from app.hardware.bme280_driver import BME280Driver
from app.models.domain.bme280_reading import BME280Reading


def test_get_reading_delegates_to_i2c_driver() -> None:
    # Arrange
    expected_reading = BME280Reading(
        ambient_temp_celsius=21.1,
        relative_humidity_pct=45.2,
        barometric_pressure_hpa=1001.3,
    )
    mock_i2c_driver = MagicMock()
    mock_i2c_driver.get_bme280_reading = AsyncMock(
        return_value=expected_reading
    )
    sensor = BME280Driver(i2c_driver=mock_i2c_driver)

    # Act
    reading = asyncio.run(sensor.get_reading())

    # Assert
    assert reading is expected_reading
    mock_i2c_driver.get_bme280_reading.assert_called_once()
