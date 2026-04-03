import random

from app.models.domain.bme280_reading import BME280Reading


class BME280:
    def __init__(self):
        # Initialize the BME280 sensor here (e.g., set up I2C communication)
        pass

    def get_reading(self) -> BME280Reading:
        # Placeholder value for testing
        return BME280Reading(
            ambient_temp_celsius=random.uniform(20.0, 25.0),
            relative_humidity_pct=random.uniform(20.0, 25.0),
            barometric_pressure_hpa=random.uniform(20.0, 25.0))
