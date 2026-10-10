import adafruit_tsl2591

from app.hardware.driver_protocols import HardwareDriverProtocol
from app.hardware.i2c_bus import I2CBus
from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591Driver(HardwareDriverProtocol[TSL2591Reading]):
    """Light sensor on the shared I2C bus."""

    def __init__(self, bus: I2CBus):
        self._bus = bus
        self._sensor = bus.run_sync(lambda: adafruit_tsl2591.TSL2591(bus.raw))

    async def get_reading(self) -> TSL2591Reading:
        return await self._bus.run(self._read)

    def _read(self) -> TSL2591Reading:
        # Runs on the I2C thread
        return TSL2591Reading(luminous_flux=self._sensor.lux)
