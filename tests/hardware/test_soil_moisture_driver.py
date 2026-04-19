import asyncio
from unittest.mock import AsyncMock, patch

from app.hardware.soil_moisture_driver import SoilMoistureDriver
from app.models.domain.soil_moisture_reading import SoilMoistureReading


@patch(
    "app.hardware.soil_moisture_driver.asyncio.sleep",
    new_callable=AsyncMock,
)
@patch("app.hardware.soil_moisture_driver.DigitalOutputDevice")
@patch("app.hardware.soil_moisture_driver.MCP3008")
def test_get_reading_powers_sensor_and_maps_adc_value(
    mock_mcp3008,
    mock_power_device,
    mock_sleep,
) -> None:
    # Arrange
    mock_mcp3008.return_value.value = 0.73
    sensor = SoilMoistureDriver()

    # Act
    reading = asyncio.run(sensor.get_reading())

    # Assert
    assert isinstance(reading, SoilMoistureReading)
    assert reading.soil_hydration == 0.73
    mock_mcp3008.assert_called_once_with(channel=0)
    mock_power_device.assert_called_once_with(18)
    mock_power_device.return_value.on.assert_called_once_with()
    mock_sleep.assert_called_once_with(0.1)
    mock_power_device.return_value.off.assert_called_once_with()
