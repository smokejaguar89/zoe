from adafruit_bme280 import basic as adafruit_bme280

from app.hardware.locked_i2c_bus import LockedI2CBus
from app.models.domain.bme280_reading import BME280Reading


class BME280Driver:
    # Keep this driver as a DI singleton. Multiple instances can appear
    # to work, but they still share the same physical I2C bus/device and
    # can contend under concurrent access.
    def __init__(self, i2c_bus: LockedI2CBus):
        self._i2c_bus = i2c_bus
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(
            i2c_bus.raw_bus,
            address=0x76,
        )

    def get_reading(self) -> BME280Reading:
        def _read() -> BME280Reading:
            return BME280Reading(
                ambient_temp_celsius=self.bme280.temperature,
                relative_humidity_pct=self.bme280.relative_humidity,
                barometric_pressure_hpa=self.bme280.pressure
            )

        return self._i2c_bus.run(_read)
