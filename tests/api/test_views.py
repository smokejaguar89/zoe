import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.views import load_homepage
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService
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
    mock_templates.TemplateResponse.return_value = "rendered-page"

    response = asyncio.run(
        load_homepage(
            request=request,
            sensor_service=sensor_service,
            analytics_service=analytics_service,
        )
    )

    assert response == "rendered-page"
    mock_templates.TemplateResponse.assert_called_once_with(
        request=request,
        name="homepage.html",
        context={
            "sensor_data": sensor_snapshot,
            "time_series": [],
            "data_points": [],
        },
    )
