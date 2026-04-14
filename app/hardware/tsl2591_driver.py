from app.hardware.driver_protocols import HardwareDriverProtocol
from app.hardware.i2c_driver import I2CDriver
from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591Driver(HardwareDriverProtocol[TSL2591Reading]):
    # The shared I2C driver serializes access and owns the underlying sensor.
    def __init__(self, ic2_driver: I2CDriver):
        self.ic2_driver = ic2_driver

    def get_reading(self) -> TSL2591Reading:
        return self.ic2_driver.get_tsl2591_reading()
