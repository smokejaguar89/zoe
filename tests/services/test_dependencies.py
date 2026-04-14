import importlib
from unittest.mock import patch, sentinel

from app import dependencies
from app.hardware.fake_drivers import (
    FakeBME280Driver,
    FakeI2CDriver,
    FakeSoilMoistureDriver,
    FakeTSL2591Driver,
)


def reload_dependencies():
    return importlib.reload(dependencies)


def test_dependency_providers_use_fake_drivers_in_test_mode(monkeypatch):
    # Arrange
    monkeypatch.setenv("SENSOR_MODE", "TEST")
    reloaded_dependencies = reload_dependencies()

    # Act
    i2c_bus = reloaded_dependencies.get_i2c_bus()
    bme280 = reloaded_dependencies.get_bme280_driver()
    tsl2591 = reloaded_dependencies.get_tsl2591_driver()
    soil_moisture = reloaded_dependencies.get_soil_moisture_driver()

    # Assert
    assert isinstance(i2c_bus, FakeI2CDriver)
    assert isinstance(bme280, FakeBME280Driver)
    assert isinstance(tsl2591, FakeTSL2591Driver)
    assert isinstance(soil_moisture, FakeSoilMoistureDriver)


def test_i2c_driver_providers_share_one_i2c_bus(monkeypatch):
    # Arrange
    monkeypatch.delenv("SENSOR_MODE", raising=False)
    reloaded_dependencies = reload_dependencies()

    with (
        patch(
            "app.hardware.i2c_driver.board.I2C",
            return_value=object(),
        ),
        patch.object(
            reloaded_dependencies,
            "BME280Driver",
        ) as mock_bme280_driver,
        patch.object(
            reloaded_dependencies,
            "TSL2591Driver",
        ) as mock_tsl2591_driver,
    ):
        mock_bme280_driver.side_effect = lambda ic2_driver: type(
            "StubBME280Driver",
            (),
            {"_ic2_driver": ic2_driver},
        )()
        mock_tsl2591_driver.side_effect = lambda ic2_driver: type(
            "StubTSL2591Driver",
            (),
            {"_ic2_driver": ic2_driver},
        )()

        # Act
        bme280 = reloaded_dependencies.get_bme280_driver()
        tsl2591 = reloaded_dependencies.get_tsl2591_driver()

        # Assert
        assert bme280._ic2_driver is tsl2591._ic2_driver


def test_soil_moisture_driver_provider_is_singleton(
    monkeypatch,
):
    # Arrange
    monkeypatch.delenv("SENSOR_MODE", raising=False)
    reloaded_dependencies = reload_dependencies()

    with patch.object(
        reloaded_dependencies,
        "SoilMoistureDriver",
    ) as mock_soil_moisture_driver:
        mock_soil_moisture_driver.return_value = sentinel.soil_moisture_driver

        # Act
        first = reloaded_dependencies.get_soil_moisture_driver()
        second = reloaded_dependencies.get_soil_moisture_driver()

        # Assert
        assert first is second
        assert first is sentinel.soil_moisture_driver
        mock_soil_moisture_driver.assert_called_once_with()
