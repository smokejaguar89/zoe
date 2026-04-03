from dataclasses import dataclass


@dataclass
class BME280Reading:
    ambient_temp_celsius: float
    relative_humidity_pct: float
    barometric_pressure_hpa: float
