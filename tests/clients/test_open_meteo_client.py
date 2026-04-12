from unittest.mock import MagicMock, patch

import pytest
import requests

from app.clients.open_meteo_client import (
    OpenMeteoClient,
    OpenMeteoClientException,
)
from app.models.domain.weather_snapshot import WeatherCode


def test_get_current_weather_zurich_returns_weather_snapshot() -> None:
    # Arrange
    client = OpenMeteoClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {
            "weather_code": 2,
            "wind_speed_10m": 4.2,
            "temperature_2m": 21.3,
            "is_day": 1,
            "precipitation": 0.1,
            "rain": 0.0,
            "showers": 0.1,
            "snowfall": 0.0,
            "cloud_cover": 42,
        },
        "current_time": "2026-04-12T10:00",
    }

    # Act
    with patch(
        "app.clients.open_meteo_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        weather = client.get_current_weather_zurich()

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
    assert weather.timestamp == "2026-04-12T10:00"

    mock_get.assert_called_once_with(
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

    # Act
    with (
        patch(
            "app.clients.open_meteo_client.requests.get",
            return_value=mock_response,
        ),
        pytest.raises(OpenMeteoClientException) as error,
    ):
        client.get_current_weather_zurich()

    # Assert
    assert str(error.value) == "Error fetching weather data: 503"


def test_get_current_weather_zurich_raises_for_request_exception() -> None:
    # Arrange
    client = OpenMeteoClient()

    # Act
    with (
        patch(
            "app.clients.open_meteo_client.requests.get",
            side_effect=requests.RequestException("network down"),
        ),
        pytest.raises(OpenMeteoClientException) as error,
    ):
        client.get_current_weather_zurich()

    # Assert
    assert str(error.value) == "Error fetching weather data: network down"
