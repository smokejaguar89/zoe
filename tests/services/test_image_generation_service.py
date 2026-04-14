import asyncio
from datetime import datetime
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.image_generation_service import (
    DayPhase,
    ImageGenerationServiceError,
    ImageGenerationService,
)

_WEATHER_OVERVIEW = (
    "The current weather: clear sky. The temperature outside is 20.0°C."
)


def _make_open_meteo_client_mock() -> MagicMock:
    mock_weather = MagicMock()
    mock_weather.weather_code.name = "CLEAR_SKY"
    mock_weather.temperature = 20.0
    mock_weather.sunrise = datetime(2026, 4, 9, 6, 0)
    mock_weather.sunset = datetime(2026, 4, 9, 20, 0)
    client = MagicMock()
    client.get_current_weather_zurich = AsyncMock(return_value=mock_weather)
    return client


def _make_news_api_client_mock(
    *,
    headlines=None,
) -> MagicMock:
    client = MagicMock()
    if headlines is None:
        headlines = ["Default Story"]
    client.get_top_headlines = AsyncMock(return_value=headlines)
    return client


def test_get_latest_generated_image_returns_database_value() -> None:
    # Arrange
    expected = MagicMock()
    database = MagicMock()
    database.get_latest_generated_image = AsyncMock(return_value=expected)
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=database,
        news_api_client=_make_news_api_client_mock(),
        open_meteo_client=_make_open_meteo_client_mock(),
    )

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image == expected
    database.get_latest_generated_image.assert_awaited_once_with()


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_generate_and_save_image_uses_exact_healthy_prompt(
    mock_datetime,
    _mock_random,
) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=0.7,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = AsyncMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = AsyncMock(return_value=["Story 1"])
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "Incorporate the following details about the plant's current state: "
        "#1: Keep the sunflower healthy and the soil well hydrated. "
        "#2: Use soft, natural indoor lighting. "
        "#3: Keep a neutral, comfortable atmosphere in the image. "
        "#4: Make the scene look like it's day. "
        "Incorporate the following information to update the "
        "background landscape: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the background landscape "
        "to incorporate this story: Story 1. "
        "Do not use words. Be creative. "
        "Finally: Don't include any people in the image."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_generate_and_save_image_uses_exact_stressed_prompt(
    mock_datetime,
    _mock_random,
) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=18.0,
        humidity=45.0,
        light=12.0,
        moisture=0.1,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = AsyncMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = AsyncMock(return_value=["Story 1"])
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 2, 15)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "Incorporate the following details about the plant's current state: "
        "#1: Make the sunflower wilt and the soil appear dry. "
        "#2: Dim the scene to suggest a dark room. "
        "#3: Add a cool, chilly atmosphere to the image. "
        "#4: Make the scene look like it's night. "
        "Incorporate the following information to update the "
        "background landscape: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the background landscape "
        "to incorporate this story: Story 1. "
        "Do not use words. Be creative. "
        "Finally: Don't include any people in the image."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


def test_get_latest_generated_image_returns_none_when_database_empty() -> None:
    # Arrange
    database = MagicMock()
    database.get_latest_generated_image = AsyncMock(return_value=None)
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=database,
        news_api_client=_make_news_api_client_mock(),
        open_meteo_client=_make_open_meteo_client_mock(),
    )

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image is None
    database.get_latest_generated_image.assert_awaited_once_with()
