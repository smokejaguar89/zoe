from app.hardware.driver_protocols import HardwareDriverProtocol
from app.hardware.i2c_driver import I2CDriver
from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591Driver(HardwareDriverProtocol[TSL2591Reading]):
    # The shared I2C driver serializes access and owns the underlying sensor.
    def __init__(self, i2c_driver: I2CDriver):
        self.i2c_driver = i2c_driver

    async def get_reading(self) -> TSL2591Reading:
        return await self.i2c_driver.get_tsl2591_reading()
