import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.dto.get_sensor_data_response import GetSensorDataResponse
from app.models.dto.get_eink_pull_response import (
    GetEinkPullResponse,
    GetEinkPullResponseData,
)
from app.models.dto.get_eink_signal_response import GetEinkSignalResponse
from app.models.dto.get_time_series_response import (
    GetTimeSeriesResponse,
    SensorSnapshotDto,
)
from app.dependencies import (
    get_analytics_service,
    get_image_generation_service,
    get_sensor_service,
)
from app.services.analytics_service import (
    AnalyticsService,
    CalculationError,
    TimeGroup,
)
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService
from app.scheduler.scheduler import IMAGE_GEN_CRON_SCHEDULE

logger = logging.getLogger(__name__)

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
    group_by: TimeGroup = TimeGroup.DAY,
):
    snapshots = await analytics_service.get_last_week_snapshots(
        group_by=group_by
    )
    snapshot_dtos = [
        SensorSnapshotDto.model_validate(snapshot) for snapshot in snapshots
    ]
    return GetTimeSeriesResponse(snapshots=snapshot_dtos)


@router.get("/images/eink_signal", response_model=GetEinkSignalResponse)
async def get_eink_signal(success: bool):
    if success:
        logger.info("New image set on eInk display.")
    else:
        logger.warning("Failed to set new image on eInk display.")

    return GetEinkSignalResponse(
        status=status.HTTP_200_OK, message="Feedback recorded"
    )


@router.get("/images/eink_pull", response_model=GetEinkPullResponse)
async def get_eink_pull(
    response: Response,
    image_generation_service: ImageGenerationService = Depends(
        get_image_generation_service
    ),
):
    metadata = await image_generation_service.get_latest_generated_image()
    next_pull_time = await get_next_pull_time()

    if not metadata:
        response.status_code = status.HTTP_204_NO_CONTENT
        pull_response = GetEinkPullResponse(
            status=status.HTTP_204_NO_CONTENT,
            message="No image available",
            data=GetEinkPullResponseData(
                next_cron_time=next_pull_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                image_url=None,
            ),
        )
        logger.info("Failed: %s", pull_response)
        return pull_response

    RASPBERRY_PI_DOMAIN = "http://192.168.86.26:8000"
    file_path = f"{RASPBERRY_PI_DOMAIN}/static/img/gemini_optimised/{metadata.filename}"

    logger.info("Getting image at %s.", file_path)

    pull_response = GetEinkPullResponse(
        status=status.HTTP_200_OK,
        type="SHOW",
        message="Image retrieved successfully",
        data=GetEinkPullResponseData(
            next_cron_time=next_pull_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            image_url=file_path,
        ),
    )
    logger.info("Success: %s", pull_response)
    return pull_response


async def get_next_pull_time() -> datetime:
    now = datetime.now(ZoneInfo("Europe/Zurich"))
    for hour in IMAGE_GEN_CRON_SCHEDULE:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        # Add buffer to ensure the image is ready
        candidate = candidate + timedelta(minutes=10)
        if candidate > now + timedelta(minutes=1):
            return candidate.astimezone(timezone.utc)
    # If no more slots today, go to the first slot tomorrow
    tomorrow_first = now.replace(
        hour=IMAGE_GEN_CRON_SCHEDULE[0], minute=0, second=0, microsecond=0
    )
    # Add buffer to ensure the image is ready
    tomorrow_first = tomorrow_first + timedelta(minutes=10)
    return tomorrow_first.astimezone(timezone.utc) + timedelta(days=1)
