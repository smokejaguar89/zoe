from unittest.mock import MagicMock, patch

from app.hardware.bme280_driver import BME280Driver
from app.models.domain.bme280_reading import BME280Reading


@patch("app.hardware.bme280_driver.adafruit_bme280.Adafruit_BME280_I2C")
@patch("app.hardware.bme280_driver.board.I2C")
def test_get_reading_returns_bme280_reading(
    mock_i2c,
    mock_bme280_ctor,
) -> None:
    mock_sensor = MagicMock()
    mock_sensor.temperature = 21.1
    mock_sensor.relative_humidity = 45.2
    mock_sensor.pressure = 1001.3
    mock_bme280_ctor.return_value = mock_sensor

    sensor = BME280Driver()

    reading = sensor.get_reading()

    assert isinstance(reading, BME280Reading)
    assert reading.ambient_temp_celsius == 21.1
    assert reading.relative_humidity_pct == 45.2
    assert reading.barometric_pressure_hpa == 1001.3
    mock_i2c.assert_called_once_with()
    mock_bme280_ctor.assert_called_once_with(
        mock_i2c.return_value,
        address=0x76,
    )
