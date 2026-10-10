from adafruit_bme280 import basic as adafruit_bme280

from app.hardware.driver_protocols import HardwareDriverProtocol
from app.hardware.i2c_bus import I2CBus
from app.models.domain.bme280_reading import BME280Reading


class BME280Driver(HardwareDriverProtocol[BME280Reading]):
    """Temperature, humidity and pressure sensor on the shared I2C bus."""

    ADDRESS = 0x76

    def __init__(self, bus: I2CBus):
        self._bus = bus
        self._sensor = bus.run_sync(
            lambda: adafruit_bme280.Adafruit_BME280_I2C(
                bus.raw, address=self.ADDRESS
            )
        )

    async def get_reading(self) -> BME280Reading:
        return await self._bus.run(self._read)

    def _read(self) -> BME280Reading:
        # Runs on the I2C thread
        return BME280Reading(
            ambient_temp_celsius=self._sensor.temperature,
            relative_humidity_pct=self._sensor.relative_humidity,
            barometric_pressure_hpa=self._sensor.pressure,
        )
