from app import dependencies
from app.hardware.fake_drivers import (
    FakeBME280Driver,
    FakeSparkfunDriver,
    FakeTSL2591Driver,
)


def test_dependency_providers_use_fake_drivers_in_test_mode(monkeypatch):
    # Arrange
    monkeypatch.setenv("SENSOR_MODE", "TEST")
    dependencies.get_bme280_driver.cache_clear()
    dependencies.get_tsl2591_driver.cache_clear()
    dependencies.get_sparkfun_driver.cache_clear()

    # Act
    bme280 = dependencies.get_bme280_driver()
    tsl2591 = dependencies.get_tsl2591_driver()
    sparkfun = dependencies.get_sparkfun_driver()

    # Assert
    assert isinstance(bme280, FakeBME280Driver)
    assert isinstance(tsl2591, FakeTSL2591Driver)
    assert isinstance(sparkfun, FakeSparkfunDriver)
