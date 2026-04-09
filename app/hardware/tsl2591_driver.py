import board
import adafruit_tsl2591

from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591Driver:
    def __init__(self):
        i2c = board.I2C()
        self.tsl2591 = adafruit_tsl2591.TSL2591(i2c)

    def get_reading(self) -> TSL2591Reading:
        return TSL2591Reading(luminous_flux=self.tsl2591.lux)
