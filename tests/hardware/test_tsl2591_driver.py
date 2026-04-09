from unittest.mock import MagicMock, patch

from app.hardware.tsl2591_driver import TSL2591Driver
from app.models.domain.tsl2591_reading import TSL2591Reading


@patch("app.hardware.tsl2591_driver.adafruit_tsl2591.TSL2591")
@patch("app.hardware.tsl2591_driver.board.I2C")
def test_get_reading_returns_tsl2591_reading(mock_i2c, mock_tsl_ctor) -> None:
    mock_sensor = MagicMock()
    mock_sensor.lux = 24.3
    mock_tsl_ctor.return_value = mock_sensor

    sensor = TSL2591Driver()

    reading = sensor.get_reading()

    assert isinstance(reading, TSL2591Reading)
    assert reading.luminous_flux == 24.3
    mock_i2c.assert_called_once_with()
    mock_tsl_ctor.assert_called_once_with(mock_i2c.return_value)
