from unittest.mock import patch

from app.hardware.tsl2591 import TSL2591
from app.models.domain.tsl2591_reading import TSL2591Reading


@patch("app.hardware.tsl2591.random.uniform", return_value=24.3)
def test_get_reading_returns_tsl2591_reading(mock_uniform) -> None:
    sensor = TSL2591()

    reading = sensor.get_reading()

    assert isinstance(reading, TSL2591Reading)
    assert reading.luminous_flux == 24.3
    mock_uniform.assert_called_once_with(20.0, 25.0)
