import random

from app.models.domain.sparkfun_reading import SparkfunReading


class Sparkfun:
    def __init__(self):
        # Initialize the Sparkfun sensor here (e.g., set up I2C communication)
        pass

    def get_reading(self) -> SparkfunReading:
        # Placeholder value for testing
        return SparkfunReading(soil_hydration=random.uniform(20.0, 25.0))
