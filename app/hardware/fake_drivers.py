import random

from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.sparkfun_reading import SparkfunReading
from app.models.domain.tsl2591_reading import TSL2591Reading


class FakeBME280Driver:
    def get_reading(self) -> BME280Reading:
        return BME280Reading(
            ambient_temp_celsius=random.uniform(18.0, 28.0),
            relative_humidity_pct=random.uniform(35.0, 65.0),
            barometric_pressure_hpa=random.uniform(1005.0, 1018.0),
        )


class FakeTSL2591Driver:
    def get_reading(self) -> TSL2591Reading:
        return TSL2591Reading(luminous_flux=random.uniform(1.0, 300.0))


class FakeSparkfunDriver:
    def get_reading(self) -> SparkfunReading:
        return SparkfunReading(soil_hydration=random.uniform(10.0, 45.0))
