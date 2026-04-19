import random
import threading
from _thread import LockType
from typing import Callable, TypeVar

from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.soil_moisture_reading import SoilMoistureReading
from app.models.domain.tsl2591_reading import TSL2591Reading

T = TypeVar("T")

# Keep singleton lifecycle in DI to mirror production wiring and
# concurrency behavior in tests.


class FakeI2CDriver:
    def __init__(self, bus=None, lock: LockType | None = None):
        self.raw_bus = bus if bus is not None else object()
        self._lock = lock or threading.Lock()

    def run(self, operation: Callable[[], T]) -> T:
        with self._lock:
            return operation()

    def get_bme280_reading(self):
        return BME280Reading(
            ambient_temp_celsius=random.uniform(18.0, 28.0),
            relative_humidity_pct=random.uniform(35.0, 65.0),
            barometric_pressure_hpa=random.uniform(1005.0, 1018.0),
        )

    def get_tsl2591_reading(self):
        from app.models.domain.tsl2591_reading import TSL2591Reading

        return TSL2591Reading(luminous_flux=random.uniform(1.0, 300.0))


class FakeBME280Driver:
    def __init__(self, i2c_driver=None):
        self._i2c_driver = i2c_driver

    def get_reading(self) -> BME280Reading:
        return BME280Reading(
            ambient_temp_celsius=random.uniform(18.0, 28.0),
            relative_humidity_pct=random.uniform(35.0, 65.0),
            barometric_pressure_hpa=random.uniform(1005.0, 1018.0),
        )


class FakeTSL2591Driver:
    def __init__(self, i2c_driver=None):
        self._i2c_driver = i2c_driver

    def get_reading(self) -> TSL2591Reading:
        return TSL2591Reading(luminous_flux=random.uniform(1.0, 300.0))


class FakeSoilMoistureDriver:
    async def get_reading(self) -> SoilMoistureReading:
        return SoilMoistureReading(soil_hydration=random.uniform(0.1, 0.9))
