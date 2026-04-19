import asyncio

from gpiozero import MCP3008, DigitalOutputDevice

from app.models.domain.soil_moisture_reading import SoilMoistureReading


class SoilMoistureDriver:
    # Keep this driver as a DI singleton. The power pin is shared state,
    # so concurrent callers can race on on()/off() without one instance
    # and one lock controlling access.
    def __init__(self):
        self.mcp3008 = MCP3008(channel=0)
        # GPIO pin 18 for power control
        self.sparkfun_power = DigitalOutputDevice(18)
        # The singleton is shared by API and scheduler threads/tasks.
        # Serialize reads so sensor power transitions cannot interleave.
        self._lock = asyncio.Lock()

    async def get_reading(self) -> SoilMoistureReading:
        async with self._lock:
            self.sparkfun_power.on()
            try:
                await asyncio.sleep(0.1)  # Wait for the sensor to stabilize
                reading = SoilMoistureReading(
                    soil_hydration=self.mcp3008.value)
            finally:
                # Power off the sensor to prevent corrosion (even if the
                # read fails).
                self.sparkfun_power.off()
            return reading
