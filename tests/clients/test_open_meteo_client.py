import asyncio
from datetime import datetime, timezone

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
        },
        "daily": {
            "sunrise": ["2026-04-12T06:30"],
            "sunset": ["2026-04-12T20:10"],
        },
    }

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    # Act
    with patch("app.clients.http_retry.httpx.AsyncClient") as MockAsyncClient:
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
    # Open-Meteo returns Zurich local times (CEST, UTC+2)
    assert weather.sunrise == datetime(2026, 4, 12, 4, 30, tzinfo=timezone.utc)
    assert weather.sunset == datetime(2026, 4, 12, 18, 10, tzinfo=timezone.utc)
    assert weather.timestamp == datetime(
        2026, 4, 12, 8, 0, tzinfo=timezone.utc
    )

    MockAsyncClient.assert_called_once_with(
        timeout=client.REQUEST_TIMEOUT_SECONDS
    )
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
            "daily": "sunrise,sunset",
            "timezone": "Europe/Zurich",
        },
    )


def _patch_http(responses):
    """Patch httpx so successive GETs return (or raise) the given items."""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=responses)
    client_patch = patch("app.clients.http_retry.httpx.AsyncClient")
    MockAsyncClient = client_patch.start()
    MockAsyncClient.return_value.__aenter__ = AsyncMock(
        return_value=mock_http_client
    )
    MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
    return client_patch, mock_http_client


def _error_response(status_code: int, text: str) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    return response


def test_get_current_weather_zurich_retries_503_then_raises() -> None:
    # Arrange
    client = OpenMeteoClient()
    client_patch, mock_http_client = _patch_http(
        [_error_response(503, "Service Unavailable")] * client.MAX_ATTEMPTS
    )

    # Act
    try:
        with patch(
            "app.clients.http_retry.asyncio.sleep", new=AsyncMock()
        ) as sleep_mock:
            with pytest.raises(OpenMeteoClientError) as error:
                asyncio.run(client.get_current_weather_zurich())
    finally:
        client_patch.stop()

    # Assert: retried with doubling waits, and the error says why
    assert mock_http_client.get.call_count == client.MAX_ATTEMPTS
    assert [call.args[0] for call in sleep_mock.await_args_list] == [1.0, 2.0]
    assert str(error.value) == (
        "Error fetching weather data: 503 - Service Unavailable"
    )


def test_get_current_weather_zurich_recovers_after_503() -> None:
    # Arrange
    client = OpenMeteoClient()
    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.json.return_value = {
        "current": {"time": "2026-04-12T10:00", "weather_code": 0},
        "daily": {
            "sunrise": ["2026-04-12T06:30"],
            "sunset": ["2026-04-12T20:10"],
        },
    }
    client_patch, mock_http_client = _patch_http(
        [_error_response(503, "Service Unavailable"), ok_response]
    )

    # Act
    try:
        with patch("app.clients.http_retry.asyncio.sleep", new=AsyncMock()):
            weather = asyncio.run(client.get_current_weather_zurich())
    finally:
        client_patch.stop()

    # Assert
    assert mock_http_client.get.call_count == 2
    assert weather.weather_code == WeatherCode.CLEAR_SKY


def test_get_current_weather_zurich_does_not_retry_client_errors() -> None:
    # Arrange
    client = OpenMeteoClient()
    client_patch, mock_http_client = _patch_http(
        [_error_response(400, '{"reason": "Invalid model"}')]
    )

    # Act
    try:
        with pytest.raises(OpenMeteoClientError) as error:
            asyncio.run(client.get_current_weather_zurich())
    finally:
        client_patch.stop()

    # Assert
    assert mock_http_client.get.call_count == 1
    assert str(error.value) == (
        'Error fetching weather data: 400 - {"reason": "Invalid model"}'
    )


def test_get_current_weather_zurich_raises_for_request_exception() -> None:
    # Arrange
    client = OpenMeteoClient()
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(
        side_effect=httpx.RequestError("network down")
    )

    # Act
    with (
        patch("app.clients.http_retry.httpx.AsyncClient") as MockAsyncClient,
        patch("app.clients.http_retry.asyncio.sleep", new=AsyncMock()),
    ):
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(OpenMeteoClientError) as error:
            asyncio.run(client.get_current_weather_zurich())

    # Assert
    assert str(error.value) == "Error fetching weather data: network down"


def test_get_current_weather_zurich_retries_then_succeeds() -> None:
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
        },
        "daily": {
            "sunrise": ["2026-04-12T06:30"],
            "sunset": ["2026-04-12T20:10"],
        },
    }
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(
        side_effect=[
            httpx.ReadTimeout("timeout"),
            mock_response,
        ]
    )

    # Act
    with (
        patch("app.clients.http_retry.httpx.AsyncClient") as MockAsyncClient,
        patch(
            "app.clients.http_retry.asyncio.sleep",
            new=AsyncMock(),
        ) as sleep_mock,
    ):
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        weather = asyncio.run(client.get_current_weather_zurich())

    # Assert
    assert weather.temperature == 21.3
    assert mock_http_client.get.call_count == 2
    sleep_mock.assert_awaited_once_with(client.RETRY_DELAY_SECONDS)


def test_get_current_weather_zurich_raises_after_max_attempts() -> None:
    # Arrange
    client = OpenMeteoClient()
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))

    # Act
    with (
        patch("app.clients.http_retry.httpx.AsyncClient") as MockAsyncClient,
        patch(
            "app.clients.http_retry.asyncio.sleep",
            new=AsyncMock(),
        ) as sleep_mock,
    ):
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(OpenMeteoClientError) as error:
            asyncio.run(client.get_current_weather_zurich())

    # Assert
    assert str(error.value) == "Error fetching weather data: timeout"
    assert mock_http_client.get.call_count == client.MAX_ATTEMPTS
    assert sleep_mock.await_count == client.MAX_ATTEMPTS - 1
