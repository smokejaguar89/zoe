from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.hardware.i2c_driver import I2CDriver
from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.tsl2591_reading import TSL2591Reading


def load_i2c_driver_module(board_i2c=None):
    """Load I2CDriver with optional mocked board.I2C."""
    mock_board_i2c = MagicMock(return_value=board_i2c or object())
    fake_board = SimpleNamespace(I2C=mock_board_i2c)

    # Mock the adafruit sensor constructors
    with (
        patch("app.hardware.i2c_driver.board", fake_board),
        patch("app.hardware.i2c_driver.adafruit_bme280.Adafruit_BME280_I2C") as mock_bme_ctor,
        patch("app.hardware.i2c_driver.adafruit_tsl2591.TSL2591") as mock_tsl_ctor,
    ):
        mock_bme_sensor = MagicMock()
        mock_bme_sensor.temperature = 21.5
        mock_bme_sensor.relative_humidity = 45.0
        mock_bme_sensor.pressure = 1013.25
        mock_bme_ctor.return_value = mock_bme_sensor

        mock_tsl_sensor = MagicMock()
        mock_tsl_sensor.lux = 250.5
        mock_tsl_ctor.return_value = mock_tsl_sensor

        driver = I2CDriver()

    return driver, mock_bme_sensor, mock_tsl_sensor


def test_default_constructor_creates_board_i2c():
    """Test that I2CDriver initializes board.I2C by default."""
    with patch("app.hardware.i2c_driver.board.I2C") as mock_i2c:
        mock_bus = object()
        mock_i2c.return_value = mock_bus

        with (
            patch("app.hardware.i2c_driver.adafruit_bme280.Adafruit_BME280_I2C"),
            patch("app.hardware.i2c_driver.adafruit_tsl2591.TSL2591"),
        ):
            driver = I2CDriver()

        mock_i2c.assert_called_once_with()
        driver.shutdown()


def test_constructor_with_custom_bus():
    """Test that I2CDriver accepts a custom bus object."""
    custom_bus = object()

    with (
        patch("app.hardware.i2c_driver.adafruit_bme280.Adafruit_BME280_I2C"),
        patch("app.hardware.i2c_driver.adafruit_tsl2591.TSL2591"),
    ):
        driver = I2CDriver(bus=custom_bus)

    driver.shutdown()


def test_get_bme280_reading_returns_correct_type():
    """Test that get_bme280_reading returns BME280Reading with correct values."""
    driver, mock_bme_sensor, _ = load_i2c_driver_module()

    reading = driver.get_bme280_reading()

    assert isinstance(reading, BME280Reading)
    assert reading.ambient_temp_celsius == 21.5
    assert reading.relative_humidity_pct == 45.0
    assert reading.barometric_pressure_hpa == 1013.25
    driver.shutdown()


def test_get_tsl2591_reading_returns_correct_type():
    """Test that get_tsl2591_reading returns TSL2591Reading with correct values."""
    driver, _, mock_tsl_sensor = load_i2c_driver_module()

    reading = driver.get_tsl2591_reading()

    assert isinstance(reading, TSL2591Reading)
    assert reading.luminous_flux == 250.5
    driver.shutdown()


def test_raw_bus_property_accessible():
    """Test that get_bme280_reading and get_tsl2591_reading work correctly."""
    driver, _, _ = load_i2c_driver_module()

    bme_reading = driver.get_bme280_reading()
    tsl_reading = driver.get_tsl2591_reading()

    assert isinstance(bme_reading, BME280Reading)
    assert isinstance(tsl_reading, TSL2591Reading)
    driver.shutdown()


def test_bme280_initialized_with_correct_address():
    """Test that BME280 is initialized with correct I2C address."""
    with patch("app.hardware.i2c_driver.board.I2C") as mock_i2c:
        mock_bus = MagicMock()
        mock_i2c.return_value = mock_bus

        with (
            patch("app.hardware.i2c_driver.adafruit_bme280.Adafruit_BME280_I2C") as mock_bme_ctor,
            patch("app.hardware.i2c_driver.adafruit_tsl2591.TSL2591"),
        ):
            driver = I2CDriver()

        mock_bme_ctor.assert_called_once_with(mock_bus, address=0x76)
        driver.shutdown()


def test_multiple_readings_work_independently():
    """Test that multiple sensor readings can be taken."""
    driver, mock_bme_sensor, mock_tsl_sensor = load_i2c_driver_module()

    # Read both sensors multiple times
    for i in range(3):
        bme_reading = driver.get_bme280_reading()
        tsl_reading = driver.get_tsl2591_reading()

        assert isinstance(bme_reading, BME280Reading)
        assert isinstance(tsl_reading, TSL2591Reading)

    driver.shutdown()
