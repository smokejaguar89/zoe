import random

from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591:
    def __init__(self):
        # Initialize the TSL2591 sensor here (e.g., set up I2C communication)
        pass

    def get_reading(self) -> TSL2591Reading:
        # Placeholder value for testing
        return TSL2591Reading(luminous_flux=random.uniform(20.0, 25.0))
