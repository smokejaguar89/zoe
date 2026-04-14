from app.hardware.driver_protocols import HardwareDriverProtocol
from app.hardware.i2c_driver import I2CDriver
from app.models.domain.bme280_reading import BME280Reading


class BME280Driver(HardwareDriverProtocol[BME280Reading]):
    def __init__(self, ic2_driver: I2CDriver):
        self.ic2_driver = ic2_driver

    async def get_reading(self) -> BME280Reading:
        return await self.ic2_driver.get_bme280_reading()
