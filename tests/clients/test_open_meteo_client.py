import asyncio
from datetime import datetime

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.clients.open_meteo_client import (
    OpenMeteoClient,
    OpenMeteoClientError,
)
from app.models.domain.weather_snapshot import WeatherCode


def test_get_current_weather_zurich_returns_weather_snapshot() -> None:
    # Arrange
    client = OpenMeteoClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {
            "time": "2026-04-12T10:00",
            "weather_code": 2,
            "wind_speed_10m": 4.2,
            "temperature_2m": 21.3,
            "is_day": 1,
            "precipitation": 0.1,
            "rain": 0.0,
            "showers": 0.1,
            "snowfall": 0.0,
            "cloud_cover": 42,
        }
    }

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    # Act
    with patch(
        "app.clients.open_meteo_client.httpx.AsyncClient"
    ) as MockAsyncClient:
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        weather = asyncio.run(client.get_current_weather_zurich())

    # Assert
    assert weather.weather_code == WeatherCode.PARTLY_CLOUDY
    assert weather.wind_speed == 4.2
    assert weather.temperature == 21.3
    assert weather.is_day is True
    assert weather.precipitation == 0.1
    assert weather.rain == 0.0
    assert weather.showers == 0.1
    assert weather.snowfall == 0.0
    assert weather.cloud_cover == 42
    assert weather.timestamp == datetime(2026, 4, 12, 10, 0)

    mock_http_client.get.assert_called_once_with(
        client.api_url,
        params={
            "latitude": client.ZURICH_LAT,
            "longitude": client.ZURICH_LON,
            "models": "meteoswiss_icon_ch1",
            "current": (
                "wind_speed_10m,temperature_2m,is_day,precipitation,"
                "rain,showers,snowfall,weather_code,cloud_cover"
            ),
        },
    )


def test_get_current_weather_zurich_raises_for_non_200_response() -> None:
    # Arrange
    client = OpenMeteoClient()
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    # Act
    with patch(
        "app.clients.open_meteo_client.httpx.AsyncClient"
    ) as MockAsyncClient:
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(OpenMeteoClientError) as error:
            asyncio.run(client.get_current_weather_zurich())

    # Assert
    assert str(error.value) == "Error fetching weather data: 503"


def test_get_current_weather_zurich_raises_for_request_exception() -> None:
    # Arrange
    client = OpenMeteoClient()
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(
        side_effect=httpx.RequestError("network down")
    )

    # Act
    with patch(
        "app.clients.open_meteo_client.httpx.AsyncClient"
    ) as MockAsyncClient:
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(OpenMeteoClientError) as error:
            asyncio.run(client.get_current_weather_zurich())

    # Assert
    assert str(error.value) == "Error fetching weather data: network down"
