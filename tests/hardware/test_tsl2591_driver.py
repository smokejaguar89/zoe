from unittest.mock import MagicMock, patch

from app.hardware.tsl2591_driver import TSL2591Driver
from app.models.domain.tsl2591_reading import TSL2591Reading


@patch("app.hardware.tsl2591_driver.adafruit_tsl2591.TSL2591")
def test_get_reading_returns_tsl2591_reading(mock_tsl_ctor) -> None:
    # Arrange
    mock_sensor = MagicMock()
    mock_sensor.lux = 24.3
    mock_tsl_ctor.return_value = mock_sensor
    mock_i2c_bus = MagicMock()
    mock_i2c_bus.raw_bus = MagicMock()

    def run_passthrough(operation):
        return operation()

    mock_i2c_bus.run.side_effect = run_passthrough
    sensor = TSL2591Driver(i2c_bus=mock_i2c_bus)

    # Act
    reading = sensor.get_reading()

    # Assert
    assert isinstance(reading, TSL2591Reading)
    assert reading.luminous_flux == 24.3
    mock_tsl_ctor.assert_called_once_with(mock_i2c_bus.raw_bus)
    assert mock_i2c_bus.run.call_count == 1
