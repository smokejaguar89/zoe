from pathlib import Path
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
import httpx
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import asyncio

from app.models.dto.get_sensor_data_response import GetSensorDataResponse
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


@router.get("/images/eink_pull", response_class=FileResponse)
async def get_eink_image(
    background_tasks: BackgroundTasks,
    image_generation_service: ImageGenerationService = Depends(
        get_image_generation_service
    ),
):
    GENERATED_IMAGE_DIR = (
        Path(__file__).resolve().parents[1] / "static" / "img" / "gemini"
    )
    metadata = await image_generation_service.get_latest_generated_image()
    file_path = GENERATED_IMAGE_DIR / metadata.filename

    logger.info("Getting image at %s.", file_path)

    background_tasks.add_task(update_cron_time)

    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=metadata.filename,
    )


async def update_cron_time():
    BLOOMIN8_URL = "http://192.168.86.241/upstream/pull_settings"
    GET_IMAGE_URL = "http://192.168.86.26:8000/api/images"

    # Wait 5 minutes. The frame needs time to take the image and update itself,
    # during which time it may be blocked.
    await asyncio.sleep(300)

    next_pull_time = await get_next_pull_time()

    # .strftime('%Y-%m-%dT%H:%M:%SZ') is the safest way to ensure the 'Z' suffix
    iso_string = next_pull_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "upstream_on": True,
        "upstream_url": GET_IMAGE_URL,
        "token": "super_secure_token",
        "cron_time": iso_string,
    }

    try:
        response = requests.put(
            BLOOMIN8_URL,
            json=payload,
            timeout=10,
            headers={"Accept": "application/json"}
        )
        print(f"✅ Sync Update Success: {response.status_code}")
    except Exception as e:
        print(f"❌ Sync Update Failed: {e}")


async def get_next_pull_time():
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
