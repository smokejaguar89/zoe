from concurrent.futures import ThreadPoolExecutor
import board
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_tsl2591
from typing import TypeVar

from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.tsl2591_reading import TSL2591Reading

T = TypeVar("T")


class I2CDriver:
    """
    Singleton manager that executes all I2C operations on a single dedicated
    thread.
    """

    BME280_ADDRESS = 0x76

    def __init__(self, bus=None):
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="I2C_Thread")

        def _init_sensors():
            raw_bus = bus if bus is not None else board.I2C()
            self._bme280 = adafruit_bme280.Adafruit_BME280_I2C(
                raw_bus, address=self.BME280_ADDRESS)
            self._tsl2591 = adafruit_tsl2591.TSL2591(raw_bus)
            self._raw_bus = raw_bus

        # Initialize the I2C bus and sensors on the dedicated I2C thread.
        self._executor.submit(_init_sensors).result()

    def get_bme280_reading(self) -> BME280Reading:
        def _read():
            # This inner function executes ONLY on the dedicated I2C thread
            return BME280Reading(
                ambient_temp_celsius=self._bme280.temperature,
                relative_humidity_pct=self._bme280.relative_humidity,
                barometric_pressure_hpa=self._bme280.pressure,
            )

        # Submit the task to the dedicated thread and block until it returns
        return self._executor.submit(_read).result()

    def get_tsl2591_reading(self) -> TSL2591Reading:
        def _read():
            return TSL2591Reading(luminous_flux=self._tsl2591.lux)

        return self._executor.submit(_read).result()

    def shutdown(self):
        self._executor.shutdown(wait=True)
