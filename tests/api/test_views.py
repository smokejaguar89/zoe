import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.views import load_homepage
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.sensor_service import SensorService


@patch("app.api.views.templates")
def test_load_homepage_renders_template_with_sensor_data(
    mock_templates,
) -> None:
    request = MagicMock()
    sensor_snapshot = SensorSnapshot(
        temperature=23.4,
        humidity=46.5,
        light=320.0,
        moisture=19.0,
        pressure=1007.2,
    )
    sensor_service = MagicMock(spec=SensorService)
    sensor_service.get_snapshot = AsyncMock(return_value=sensor_snapshot)
    analytics_service = MagicMock(spec=AnalyticsService)
    analytics_service.get_last_week_snapshots = AsyncMock(return_value=[])
    gemini_service = MagicMock(spec=GeminiService)
    gemini_service.get_or_generate_image = AsyncMock(
        return_value=Path(
            "app/static/img/gemini/sunflower_2026-04-03:13:39.jpg"
        )
    )
    mock_templates.TemplateResponse.return_value = "rendered-page"

    response = asyncio.run(
        load_homepage(
            request=request,
            sensor_service=sensor_service,
            analytics_service=analytics_service,
            gemini_service=gemini_service,
        )
    )

    assert response == "rendered-page"
    gemini_service.get_or_generate_image.assert_awaited_once_with(
        max_age_minutes=30
    )
    mock_templates.TemplateResponse.assert_called_once_with(
        request=request,
        name="homepage.html",
        context={
            "sensor_data": sensor_snapshot,
            "time_series": [],
            "generated_image_path": (
                "/static/img/gemini/sunflower_2026-04-03:13:39.jpg"
            ),
            "generated_image_generated_at": "2026-04-03:13:39",
        },
    )


@patch("app.api.views.templates")
def test_load_homepage_handles_gemini_failure(mock_templates) -> None:
    request = MagicMock()
    sensor_snapshot = SensorSnapshot(
        temperature=23.4,
        humidity=46.5,
        light=320.0,
        moisture=19.0,
        pressure=1007.2,
    )
    sensor_service = MagicMock(spec=SensorService)
    sensor_service.get_snapshot = AsyncMock(return_value=sensor_snapshot)
    analytics_service = MagicMock(spec=AnalyticsService)
    analytics_service.get_last_week_snapshots = AsyncMock(return_value=[])
    gemini_service = MagicMock(spec=GeminiService)
    gemini_service.get_or_generate_image = AsyncMock(
        side_effect=GeminiServiceError("Gemini API request failed.")
    )
    mock_templates.TemplateResponse.return_value = "rendered-page"

    response = asyncio.run(
        load_homepage(
            request=request,
            sensor_service=sensor_service,
            analytics_service=analytics_service,
            gemini_service=gemini_service,
        )
    )

    assert response == "rendered-page"
    mock_templates.TemplateResponse.assert_called_once_with(
        request=request,
        name="homepage.html",
        context={
            "sensor_data": sensor_snapshot,
            "time_series": [],
            "generated_image_path": None,
            "generated_image_generated_at": None,
        },
    )
