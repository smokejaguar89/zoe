from datetime import datetime, timezone

from fastapi.params import Depends

from app.hardware.bme280 import BME280
from app.hardware.sparkfun import Sparkfun
from app.hardware.tsl2591 import TSL2591
from app.models.domain.sensor_snapshot import SensorSnapshot


class SensorService:
    def __init__(
            self,
            bme280=Depends(BME280),
            tsl2591=Depends(TSL2591),
            sparkfun=Depends(Sparkfun)):
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
