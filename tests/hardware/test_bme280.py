from unittest.mock import call, patch

from app.hardware.bme280 import BME280
from app.models.domain.bme280_reading import BME280Reading


@patch(
    "app.hardware.bme280.random.uniform",
    side_effect=[21.1, 45.2, 1001.3],
)
def test_get_reading_returns_bme280_reading(mock_uniform) -> None:
    sensor = BME280()

    reading = sensor.get_reading()

    assert isinstance(reading, BME280Reading)
    assert reading.ambient_temp_celsius == 21.1
    assert reading.relative_humidity_pct == 45.2
    assert reading.barometric_pressure_hpa == 1001.3
    assert mock_uniform.call_count == 3
    mock_uniform.assert_has_calls(
        [call(20.0, 25.0), call(20.0, 25.0), call(20.0, 25.0)]
    )
