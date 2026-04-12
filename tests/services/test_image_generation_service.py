import asyncio
from datetime import datetime
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.image_generation_service import (
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
    client = MagicMock()
    client.get_current_weather_zurich.return_value = mock_weather
    return client


def _make_news_api_client_mock(
    *,
    headlines=None,
) -> MagicMock:
    client = MagicMock()
    if headlines is None:
        headlines = []
    client.get_top_headlines.return_value = headlines
    return client


def test_generate_and_save_image_writes_expected_jpg_name(tmp_path) -> None:
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
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=_make_news_api_client_mock(),
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    service.generated_image_dir = tmp_path
    service.base_image_path = tmp_path / "sunflower_base.jpg"
    service.base_image_path.write_bytes(b"base-image")
    service._craft_image_prompt = MagicMock(return_value="plant prompt")
    service._timestamp_to_string = MagicMock(return_value="2026-04-03:13:39")

    # Act
    output_path = asyncio.run(service.generate_and_save_image())

    # Assert
    assert output_path.name == "sunflower_2026-04-03:13:39.jpg"
    assert output_path.read_bytes() == b"jpg-bytes"
    image_client.generate_image.assert_called_once_with(
        prompt="plant prompt",
        base_image_bytes=b"base-image",
    )
    database.save_generated_image.assert_awaited_once_with(
        filename="sunflower_2026-04-03:13:39.jpg",
        generated_at=ANY,
        snapshot=snapshot,
    )


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
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = MagicMock(return_value=["Story 1"])
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
        "#4: Make the scene look like it's afternoon. "
        "Incorporate the following information to update the "
        "background landscape: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the background landscape "
        "to incorporate this story: Story 1. "
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
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = MagicMock(return_value=["Story 1"])
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
        "Finally: Don't include any people in the image."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


def test_get_weather_overview_formats_weather_snapshot_correctly() -> None:
    # Arrange
    mock_weather = MagicMock()
    mock_weather.weather_code.name = "RAIN_MODERATE"
    mock_weather.temperature = 12.5
    open_meteo_client = MagicMock()
    open_meteo_client.get_current_weather_zurich.return_value = mock_weather
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=MagicMock(),
        news_api_client=_make_news_api_client_mock(),
        open_meteo_client=open_meteo_client,
    )

    # Act
    overview = service._get_weather_overview()

    # Assert
    assert overview == (
        "The current weather: rain moderate. "
        "The temperature outside is 12.5\u00b0C."
    )


def test_get_weather_overview_calls_open_meteo_client() -> None:
    # Arrange
    open_meteo_client = _make_open_meteo_client_mock()
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=MagicMock(),
        news_api_client=_make_news_api_client_mock(),
        open_meteo_client=open_meteo_client,
    )

    # Act
    service._get_weather_overview()

    # Assert
    open_meteo_client.get_current_weather_zurich.assert_called_once()


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


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_craft_image_prompt_includes_top_stories(
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
    image_client = MagicMock()
    database = MagicMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = MagicMock(
        return_value=[
            "Breaking: AI advances reshape tech industry",
            "Climate summit reaches historic agreement",
            "Markets surge on economic recovery",
        ]
    )
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "Incorporate the following details about the plant's current state: "
        "#1: Keep the sunflower healthy and the soil well hydrated. "
        "#2: Use soft, natural indoor lighting. "
        "#3: Keep a neutral, comfortable atmosphere in the image. "
        "#4: Make the scene look like it's afternoon. "
        "Incorporate the following information to update the "
        "background landscape: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the background landscape to incorporate this story: "
        "Breaking: AI advances reshape tech industry. "
        "Finally: Don't include any people in the image."
    )

    # Act
    prompt = service._craft_image_prompt(snapshot)

    # Assert
    assert prompt == expected_prompt
    news_api_client.get_top_headlines.assert_called_once()


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_craft_image_prompt_handles_empty_stories(
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
    image_client = MagicMock()
    database = MagicMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = MagicMock(return_value=[])
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    # Act / Assert
    with pytest.raises(
        ImageGenerationServiceError,
        match="No news stories available to include in prompt.",
    ):
        service._craft_image_prompt(snapshot)

    news_api_client.get_top_headlines.assert_called_once()


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_craft_image_prompt_handles_news_api_error(
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
    image_client = MagicMock()
    database = MagicMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = MagicMock(
        side_effect=Exception("API error")
    )
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    # Act / Assert
    with pytest.raises(Exception, match="API error"):
        service._craft_image_prompt(snapshot)

    news_api_client.get_top_headlines.assert_called_once()


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_craft_image_prompt_uses_only_first_story(
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
    image_client = MagicMock()
    database = MagicMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = MagicMock(
        return_value=[
            "Story 1",
            "Story 2",
            "Story 3",
            "Story 4",
            "Story 5",
        ]
    )
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "Incorporate the following details about the plant's current state: "
        "#1: Keep the sunflower healthy and the soil well hydrated. "
        "#2: Use soft, natural indoor lighting. "
        "#3: Keep a neutral, comfortable atmosphere in the image. "
        "#4: Make the scene look like it's afternoon. "
        "Incorporate the following information to update the "
        "background landscape: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the background landscape "
        "to incorporate this story: Story 1. "
        "Finally: Don't include any people in the image."
    )

    # Act
    prompt = service._craft_image_prompt(snapshot)

    # Assert
    assert prompt == expected_prompt
    assert "Story 1" in prompt
    assert "Story 2" not in prompt
    assert "Story 3" not in prompt
    assert "Story 4" not in prompt
    assert "Story 5" not in prompt
