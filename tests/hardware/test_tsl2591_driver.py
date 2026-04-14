from unittest.mock import MagicMock, AsyncMock
import asyncio

from app.hardware.tsl2591_driver import TSL2591Driver
from app.models.domain.tsl2591_reading import TSL2591Reading


def test_get_reading_delegates_to_ic2_driver() -> None:
    # Arrange
    expected_reading = TSL2591Reading(luminous_flux=24.3)
    mock_ic2_driver = MagicMock()
    mock_ic2_driver.get_tsl2591_reading = AsyncMock(
        return_value=expected_reading)
    sensor = TSL2591Driver(ic2_driver=mock_ic2_driver)

    # Act
    reading = asyncio.run(sensor.get_reading())

    # Assert
    assert reading is expected_reading
    mock_ic2_driver.get_tsl2591_reading.assert_called_once()
