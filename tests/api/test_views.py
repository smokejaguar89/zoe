import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.views import load_homepage
from app.models.domain.generated_image import GeneratedImage
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService


@patch("app.api.views.templates")
def test_load_homepage_renders_template_with_sensor_data(
    mock_templates,
) -> None:
    # Arrange
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
    image_snapshot = SensorSnapshot(
        temperature=18.2,
        humidity=55.1,
        light=140.0,
        moisture=12.3,
        pressure=1004.5,
    )
    image_generation_service = MagicMock(spec=ImageGenerationService)
    image_generation_service.get_latest_generated_image = AsyncMock(
        return_value=GeneratedImage(
            filename="sunflower_2026-04-03:13:39.jpg",
            generated_at=image_snapshot.timestamp,
            sensor_snapshot=image_snapshot,
        )
    )
    mock_templates.TemplateResponse.return_value = "rendered-page"

    # Act
    response = asyncio.run(
        load_homepage(
            request=request,
            sensor_service=sensor_service,
            analytics_service=analytics_service,
            image_generation_service=image_generation_service,
        )
    )

    # Assert
    assert response == "rendered-page"
    get_latest_generated_image = (
        image_generation_service.get_latest_generated_image
    )
    get_latest_generated_image.assert_awaited_once_with()
    mock_templates.TemplateResponse.assert_called_once_with(
        request=request,
        name="homepage.html",
        context={
            "sensor_data": sensor_snapshot,
            "time_series": [],
            "generated_image_path": (
                "/static/img/gemini/sunflower_2026-04-03:13:39.jpg"
            ),
            "generated_image_generated_at": (
                image_snapshot.timestamp.strftime("%Y-%m-%d:%H:%M")
            ),
            "generated_image_snapshot": image_snapshot,
        },
    )


@patch("app.api.views.templates")
def test_load_homepage_handles_missing_gemini_image(mock_templates) -> None:
    # Arrange
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
    image_generation_service = MagicMock(spec=ImageGenerationService)
    image_generation_service.get_latest_generated_image = AsyncMock(
        return_value=None
    )
    mock_templates.TemplateResponse.return_value = "rendered-page"

    # Act
    response = asyncio.run(
        load_homepage(
            request=request,
            sensor_service=sensor_service,
            analytics_service=analytics_service,
            image_generation_service=image_generation_service,
        )
    )

    # Assert
    assert response == "rendered-page"
    get_latest_generated_image = (
        image_generation_service.get_latest_generated_image
    )
    get_latest_generated_image.assert_awaited_once_with()
    mock_templates.TemplateResponse.assert_called_once_with(
        request=request,
        name="homepage.html",
        context={
            "sensor_data": sensor_snapshot,
            "time_series": [],
            "generated_image_path": None,
            "generated_image_generated_at": None,
            "generated_image_snapshot": None,
        },
    )
