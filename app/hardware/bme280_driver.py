import board
from adafruit_bme280 import basic as adafruit_bme280

from app.models.domain.bme280_reading import BME280Reading


class BME280Driver:
    def __init__(self):
        i2c = board.I2C()   # uses board.SCL and board.SDA
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

    def get_reading(self) -> BME280Reading:
        # Placeholder value for testing
        return BME280Reading(
            ambient_temp_celsius=self.bme280.temperature,
            relative_humidity_pct=self.bme280.relative_humidity,
            barometric_pressure_hpa=self.bme280.pressure
        )
