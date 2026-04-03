from typing import List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService

# 1. Point to the templates directory
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def load_homepage(
        request: Request,
        sensor_service=Depends(SensorService),
        analytics_service=Depends(AnalyticsService),
        image_generation_service=Depends(
            ImageGenerationService)) -> HTMLResponse:
    generated_image_url = None
    generated_image_generated_at = None
    generated_image_snapshot = None
    generated_image = await (
        image_generation_service.get_latest_generated_image()
    )
    if generated_image is not None:
        generated_image_url = (
            f"/static/img/gemini/{generated_image.filename}"
        )
        generated_image_generated_at = generated_image.generated_at.strftime(
            "%Y-%m-%d:%H:%M"
        )
        generated_image_snapshot = generated_image.sensor_snapshot

    # Data you want to pass to your HTML
    sensor_snapshot = await sensor_service.get_snapshot()
    snapshots: List[SensorSnapshot] = (
        await analytics_service.get_last_week_snapshots()
    )
    time_series = []
    for index, snapshot in enumerate(snapshots):
        timestamp = getattr(snapshot, "timestamp", None)
        time_label = (
            timestamp.strftime("%H:%M") if timestamp else str(index + 1)
        )
        time_series.append(
            {
                "time": time_label,
                "light": snapshot.light,
                "temp": snapshot.temperature,
                "moisture": snapshot.moisture,
                "humidity": snapshot.humidity,
                "pressure": snapshot.pressure,
            }
        )

    # 2. Return the template
    return templates.TemplateResponse(
        request=request,
        name="homepage.html",
        context={
            "sensor_data": sensor_snapshot,
            "time_series": time_series,
            "generated_image_path": generated_image_url,
            "generated_image_generated_at": generated_image_generated_at,
            "generated_image_snapshot": generated_image_snapshot,
        }
    )
