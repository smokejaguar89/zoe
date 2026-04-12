from datetime import datetime, timezone
from app.models.domain.sensor_snapshot import SensorSnapshot

# Soil hydration is normalized to [0.0, 1.0]
MOISTURE_THRESHOLD = 0.35

# TSL2591 luminous flux (lux) category boundaries
LIGHT_LOW_LUX_THRESHOLD = 20.0
LIGHT_NORMAL_LUX_UPPER_THRESHOLD = 150.0

# Indoor temperature (°C) category boundaries
TEMPERATURE_COOL_C_THRESHOLD = 20.0
TEMPERATURE_COMFORT_C_UPPER_THRESHOLD = 27.0


class SensorService:
    def __init__(self, bme280, tsl2591, soil_moisture):
        self.bme280 = bme280
        self.tsl2591 = tsl2591
        self.soil_moisture = soil_moisture

    async def get_snapshot(self) -> SensorSnapshot:
        bme280Reading = self.bme280.get_reading()
        tsl2591Reading = self.tsl2591.get_reading()
        soilMoistureReading = await self.soil_moisture.get_reading()

        return SensorSnapshot(
            temperature=bme280Reading.ambient_temp_celsius,
            humidity=bme280Reading.relative_humidity_pct,
            pressure=bme280Reading.barometric_pressure_hpa,
            light=tsl2591Reading.luminous_flux,
            moisture=soilMoistureReading.soil_hydration,
            timestamp=datetime.now(timezone.utc),
        )
