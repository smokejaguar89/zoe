import asyncio
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.api import get_last_week_average, get_sensor_data, router
from app.dependencies import get_analytics_service, get_sensor_service
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.analytics_service import AnalyticsService, CalculationError
from app.services.sensor_service import SensorService


def test_get_sensor_data_returns_valid_response_model() -> None:
    # Arrange
    service = MagicMock(spec=SensorService)
    service.get_snapshot = AsyncMock(
        return_value=SensorSnapshot(
            temperature=24.2,
            humidity=46.5,
            light=320.0,
            moisture=19.0,
            pressure=1007.2,
        )
    )

    # Act
    response = asyncio.run(get_sensor_data(sensor_service=service))

    # Assert
    assert response.temperature == 24.2
    assert response.humidity == 46.5
    assert response.light == 320.0
    assert response.moisture == 19.0


def test_sensors_route_returns_expected_payload() -> None:
    # Arrange
    service = MagicMock(spec=SensorService)
    service.get_snapshot = AsyncMock(
        return_value=SensorSnapshot(
            temperature=24.2,
            humidity=46.5,
            light=320.0,
            moisture=19.0,
            pressure=1007.2,
        )
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_sensor_service] = lambda: service
    client = TestClient(app)

    # Act
    response = client.get("/api/sensors")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "temperature": 24.2,
        "humidity": 46.5,
        "light": 320.0,
        "moisture": 19.0,
        "pressure": 1007.2,
    }


def test_get_last_week_average_returns_valid_response_model() -> None:
    # Arrange
    service = MagicMock(spec=AnalyticsService)
    service.get_last_week_average = AsyncMock(
        return_value=SensorSnapshot(
            temperature=23.5,
            humidity=44.5,
            light=300.0,
            moisture=20.5,
            pressure=1008.1,
        )
    )

    # Act
    response = asyncio.run(get_last_week_average(analytics_service=service))

    # Assert
    assert response.temperature == 23.5
    assert response.humidity == 44.5
    assert response.light == 300.0
    assert response.moisture == 20.5
    assert response.pressure == 1008.1


def test_last_week_average_route_returns_404_when_no_data() -> None:
    # Arrange
    service = MagicMock(spec=AnalyticsService)
    service.get_last_week_average = AsyncMock(
        side_effect=CalculationError(
            "No sensor readings found for the past week."
        )
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_analytics_service] = lambda: service
    client = TestClient(app)

    # Act
    response = client.get("/api/sensors/last_week_average")

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No sensor readings found for the past week."
    }
