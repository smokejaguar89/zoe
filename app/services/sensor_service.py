from datetime import datetime, timezone
import asyncio
from app.hardware.driver_protocols import HardwareDriverProtocol
from app.models.domain.bme280_reading import BME280Reading
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.models.domain.tsl2591_reading import TSL2591Reading
from app.models.domain.soil_moisture_reading import SoilMoistureReading

# Soil hydration is normalized to [0.0, 1.0]
MOISTURE_THRESHOLD = 0.35

# TSL2591 luminous flux (lux) category boundaries
LIGHT_LOW_LUX_THRESHOLD = 20.0
LIGHT_NORMAL_LUX_UPPER_THRESHOLD = 150.0

# Indoor temperature (°C) category boundaries
TEMPERATURE_COOL_C_THRESHOLD = 20.0
TEMPERATURE_COMFORT_C_UPPER_THRESHOLD = 27.0


class SensorService:
    def __init__(
            self,
            bme280: HardwareDriverProtocol[BME280Reading],
            tsl2591: HardwareDriverProtocol[TSL2591Reading],
            soil_moisture: HardwareDriverProtocol[SoilMoistureReading]):
        self.bme280 = bme280
        self.tsl2591 = tsl2591
        self.soil_moisture = soil_moisture

    async def get_snapshot(self) -> SensorSnapshot:
        (
            bme280_reading,
            tsl2591_reading,
            soil_moisture_reading,
        ) = await asyncio.gather(
            self.bme280.get_reading(),
            self.tsl2591.get_reading(),
            self.soil_moisture.get_reading(),
        )

        return SensorSnapshot(
            temperature=bme280_reading.ambient_temp_celsius,
            humidity=bme280_reading.relative_humidity_pct,
            pressure=bme280_reading.barometric_pressure_hpa,
            light=tsl2591_reading.luminous_flux,
            moisture=soil_moisture_reading.soil_hydration,
            timestamp=datetime.now(timezone.utc),
        )
