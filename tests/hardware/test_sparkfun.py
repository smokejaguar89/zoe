from unittest.mock import patch

from app.hardware.sparkfun import Sparkfun
from app.models.domain.sparkfun_reading import SparkfunReading


@patch("app.hardware.sparkfun.random.uniform", return_value=22.7)
def test_get_reading_returns_sparkfun_reading(mock_uniform) -> None:
    sensor = Sparkfun()

    reading = sensor.get_reading()

    assert isinstance(reading, SparkfunReading)
    assert reading.soil_hydration == 22.7
    mock_uniform.assert_called_once_with(20.0, 25.0)
