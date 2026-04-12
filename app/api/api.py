from fastapi import APIRouter, Depends, HTTPException

from app.models.dto.get_sensor_data_response import GetSensorDataResponse
from app.models.dto.get_time_series_response import (
    GetTimeSeriesResponse,
    SensorSnapshotDto,
)
from app.dependencies import get_analytics_service, get_sensor_service
from app.services.analytics_service import AnalyticsService, CalculationError
from app.services.sensor_service import SensorService

router = APIRouter(prefix="/api")


@router.get("/sensors", response_model=GetSensorDataResponse)
async def get_sensor_data(
    sensor_service: SensorService = Depends(get_sensor_service),
):
    sensor_snapshot = await sensor_service.get_snapshot()
    return GetSensorDataResponse.model_validate(sensor_snapshot)


@router.get("/sensors/last_week_average", response_model=GetSensorDataResponse)
async def get_last_week_average(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    try:
        average_data = await analytics_service.get_last_week_average()
    except CalculationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return GetSensorDataResponse.model_validate(average_data)


@router.get("/sensors/time_series", response_model=GetTimeSeriesResponse)
async def get_time_series(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    snapshots = await analytics_service.get_last_week_snapshots()
    snapshot_dtos = [
        SensorSnapshotDto.model_validate(snapshot) for snapshot in snapshots
    ]
    return GetTimeSeriesResponse(snapshots=snapshot_dtos)
