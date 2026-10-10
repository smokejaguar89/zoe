from datetime import datetime, timedelta
import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

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
    get_generated_image_service,
    get_sensor_service,
)
from app.services.analytics_service import (
    AnalyticsService,
    CalculationError,
    TimeGroup,
)
from app.services.generated_image_service import GeneratedImageService
from app.services.sensor_service import SensorService
from app.scheduler.scheduler import get_next_image_pull_time
from app.utils.clock import to_local, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

EINK_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


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
    request: Request,
    generated_image_service: GeneratedImageService = Depends(
        get_generated_image_service
    ),
):
    metadata = await generated_image_service.get_latest_generated_image()
    next_pull_time = get_next_image_pull_time()
    next_cron_time = next_pull_time.strftime(EINK_TIME_FORMAT)
    _log_next_eink_pull(next_pull_time)

    if metadata is None:
        logger.info("No image available yet for eInk display.")
        return GetEinkPullResponse(
            status=status.HTTP_200_OK,
            type=None,
            message="No image available",
            data=GetEinkPullResponseData(
                next_cron_time=next_cron_time,
                image_url=None,
            ),
        )

    # Build the URL from the host the display used to reach us
    image_url = str(request.base_url).rstrip("/") + (
        generated_image_service.optimised_image_url_path(metadata.filename)
    )
    logger.info("Serving eInk image at %s.", image_url)

    return GetEinkPullResponse(
        status=status.HTTP_200_OK,
        type="SHOW",
        message="Image retrieved successfully",
        data=GetEinkPullResponseData(
            next_cron_time=next_cron_time,
            image_url=image_url,
        ),
    )


def _log_next_eink_pull(next_pull_time: datetime) -> None:
    # The frame sleeps until the next_cron_time we send it, so this is when
    # it will next ask for an image
    logger.info(
        "eInk frame will next request an image at %s (in %s).",
        to_local(next_pull_time).strftime("%Y-%m-%d %H:%M %Z"),
        _format_duration(next_pull_time - utc_now()),
    )


def _format_duration(duration: timedelta) -> str:
    minutes = max(0, round(duration.total_seconds() / 60))
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"
