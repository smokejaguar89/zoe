from unittest.mock import MagicMock, patch

from app.hardware.bme280_driver import BME280Driver
from app.models.domain.bme280_reading import BME280Reading


@patch("app.hardware.bme280_driver.adafruit_bme280.Adafruit_BME280_I2C")
def test_get_reading_returns_bme280_reading(mock_bme280_ctor) -> None:
    # Arrange
    mock_sensor = MagicMock()
    mock_sensor.temperature = 21.1
    mock_sensor.relative_humidity = 45.2
    mock_sensor.pressure = 1001.3
    mock_bme280_ctor.return_value = mock_sensor
    mock_i2c_bus = MagicMock()
    mock_i2c_bus.raw_bus = MagicMock()

    def run_passthrough(operation):
        return operation()

    mock_i2c_bus.run.side_effect = run_passthrough
    sensor = BME280Driver(i2c_bus=mock_i2c_bus)

    # Act
    reading = sensor.get_reading()

    # Assert
    assert isinstance(reading, BME280Reading)
    assert reading.ambient_temp_celsius == 21.1
    assert reading.relative_humidity_pct == 45.2
    assert reading.barometric_pressure_hpa == 1001.3
    mock_bme280_ctor.assert_called_once_with(
        mock_i2c_bus.raw_bus,
        address=0x76,
    )
    assert mock_i2c_bus.run.call_count == 1
