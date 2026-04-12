import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.views import load_homepage
from app.models.domain.generated_image import GeneratedImage
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import (
    LIGHT_LOW_LUX_THRESHOLD,
    MOISTURE_THRESHOLD,
    SensorService,
    TEMPERATURE_COOL_C_THRESHOLD,
)


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
            "chart_thresholds": {
                "moisture_min": MOISTURE_THRESHOLD,
                "light_min_lux": LIGHT_LOW_LUX_THRESHOLD,
                "temperature_min_c": TEMPERATURE_COOL_C_THRESHOLD,
            },
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
            "chart_thresholds": {
                "moisture_min": MOISTURE_THRESHOLD,
                "light_min_lux": LIGHT_LOW_LUX_THRESHOLD,
                "temperature_min_c": TEMPERATURE_COOL_C_THRESHOLD,
            },
            "generated_image_path": None,
            "generated_image_generated_at": None,
            "generated_image_snapshot": None,
        },
    )


@patch("app.api.views.templates")
def test_load_homepage_includes_date_and_time_in_time_series(
    mock_templates,
) -> None:
    # Arrange
    request = MagicMock()
    sensor_service = MagicMock(spec=SensorService)
    sensor_service.get_snapshot = AsyncMock(
        return_value=SensorSnapshot(
            temperature=22.0,
            humidity=40.0,
            light=300.0,
            moisture=0.5,
            pressure=1005.0,
        )
    )
    snapshots = [
        SensorSnapshot(
            temperature=21.0,
            humidity=41.0,
            light=250.0,
            moisture=0.45,
            pressure=1004.0,
            timestamp=datetime(2026, 4, 10, 8, 30),
        ),
        SensorSnapshot(
            temperature=20.5,
            humidity=42.0,
            light=240.0,
            moisture=0.44,
            pressure=1003.5,
            timestamp=datetime(2026, 4, 11, 9, 45),
        ),
    ]
    analytics_service = MagicMock(spec=AnalyticsService)
    analytics_service.get_last_week_snapshots = AsyncMock(
        return_value=snapshots
    )
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
    template_kwargs = mock_templates.TemplateResponse.call_args.kwargs
    assert template_kwargs["context"]["time_series"] == [
        {
            "time": "2026-04-10 08:30",
            "light": 250.0,
            "temp": 21.0,
            "moisture": 0.45,
            "humidity": 41.0,
            "pressure": 1004.0,
        },
        {
            "time": "2026-04-11 09:45",
            "light": 240.0,
            "temp": 20.5,
            "moisture": 0.44,
            "humidity": 42.0,
            "pressure": 1003.5,
        },
    ]
