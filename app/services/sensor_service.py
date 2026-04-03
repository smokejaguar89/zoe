from datetime import datetime, timezone

from fastapi.params import Depends

from app.hardware.bme280_driver import BME280Driver
from app.hardware.sparkfun_driver import SparkfunDriver
from app.hardware.tsl2591_driver import TSL2591Driver
from app.models.domain.sensor_snapshot import SensorSnapshot

MOISTURE_THRESHOLD = 30.0
LIGHT_THRESHOLD = 30.0
TEMPERATURE_THRESHOLD = 25.0


class SensorService:
    def __init__(
            self,
            bme280=Depends(BME280Driver),
            tsl2591=Depends(TSL2591Driver),
            sparkfun=Depends(SparkfunDriver)):
        self.bme280 = bme280
        self.tsl2591 = tsl2591
        self.sparkfun = sparkfun

    async def get_snapshot(self) -> SensorSnapshot:
        bme280Reading = self.bme280.get_reading()
        tsl2591Reading = self.tsl2591.get_reading()
        sparkfunReading = self.sparkfun.get_reading()
        return SensorSnapshot(
            temperature=bme280Reading.ambient_temp_celsius,
            humidity=bme280Reading.relative_humidity_pct,
            pressure=bme280Reading.barometric_pressure_hpa,
            light=tsl2591Reading.luminous_flux,
            moisture=sparkfunReading.soil_hydration,
            timestamp=datetime.now(timezone.utc)
        )
