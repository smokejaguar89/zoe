import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.soil_moisture_reading import SoilMoistureReading
from app.models.domain.tsl2591_reading import TSL2591Reading
from app.services.sensor_service import SensorService


def test_get_sensor_data_maps_sensor_readings() -> None:
    # Arrange
    bme280 = MagicMock()
    bme280.get_reading = AsyncMock(
        return_value=BME280Reading(
            ambient_temp_celsius=23.0,
            relative_humidity_pct=41.5,
            barometric_pressure_hpa=1002.4,
        )
    )
    tsl2591 = MagicMock()
    tsl2591.get_reading = AsyncMock(
        return_value=TSL2591Reading(luminous_flux=312.1)
    )
    soil_moisture = MagicMock()
    soil_moisture.get_reading = AsyncMock(
        return_value=SoilMoistureReading(
            soil_hydration=17.6,
        )
    )
    service = SensorService(
        bme280=bme280,
        tsl2591=tsl2591,
        soil_moisture=soil_moisture,
        snapshot_repository=MagicMock(),
    )

    # Act
    sensor_data = asyncio.run(service.get_snapshot())

    # Assert
    assert sensor_data.temperature == 23.0
    assert sensor_data.humidity == 41.5
    assert sensor_data.pressure == 1002.4
    assert sensor_data.light == 312.1
    assert sensor_data.moisture == 17.6
    assert bme280.get_reading.call_count == 1
    assert tsl2591.get_reading.call_count == 1
    soil_moisture.get_reading.assert_awaited_once()


def test_record_snapshot_saves_the_snapshot_it_takes() -> None:
    # Arrange
    snapshot_repository = MagicMock()
    service = SensorService(
        bme280=MagicMock(),
        tsl2591=MagicMock(),
        soil_moisture=MagicMock(),
        snapshot_repository=snapshot_repository,
    )
    expected = MagicMock()
    service.get_snapshot = AsyncMock(return_value=expected)

    # Act
    snapshot = asyncio.run(service.record_snapshot())

    # Assert
    assert snapshot is expected
    snapshot_repository.add.assert_called_once_with(expected)
