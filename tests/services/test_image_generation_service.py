import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.image_generation_service import (
    ImageGenerationService,
)
from app.utils.clock import LOCAL_TIMEZONE
from app.utils.prompt_builder import ImagePromptBuilder

_WEATHER_OVERVIEW = (
    "The current weather: clear sky. The temperature outside is 20.0°C."
)


def _make_open_meteo_client_mock() -> MagicMock:
    mock_weather = MagicMock()
    mock_weather.weather_code.name = "CLEAR_SKY"
    mock_weather.temperature = 20.0
    mock_weather.sunrise = datetime(2026, 4, 9, 6, 0, tzinfo=LOCAL_TIMEZONE)
    mock_weather.sunset = datetime(2026, 4, 9, 20, 0, tzinfo=LOCAL_TIMEZONE)
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


@patch.object(
    ImageGenerationService, "_write_optimised_image", return_value=None
)
@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.utc_now")
def test_generate_and_save_image_uses_exact_healthy_prompt(
    mock_utc_now,
    _mock_random,
    _mock_write_optimised,
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
    image_repository = MagicMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = AsyncMock(return_value=["Story 1"])
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        image_repository=image_repository,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
        prompt_builder=ImagePromptBuilder(),
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    # 14:30 in Zurich
    mock_utc_now.return_value = datetime(
        2026, 4, 9, 12, 30, tzinfo=timezone.utc
    )
    expected_prompt = (
        "Use the provided painting as the base image: a Van Gogh-style "
        "view across Zurich rooftops towards the Uetliberg, with a "
        "potted plant on the rooftop ledge on the right. Keep the "
        "composition, the swirling brushwork and the TV tower on the "
        "hill. Edit the scene to reflect the plant's environment. "
        "Incorporate the following details about the plant's current state: "
        "#1: Keep the potted plant healthy and its soil well hydrated. "
        "#2: Light the potted plant with soft, gentle light. "
        "#3: Keep a neutral, comfortable atmosphere in the image. "
        "#4: Make the scene look like it's day. "
        "Incorporate the following information to update "
        "the sky and the hillside: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the sky and the hillside "
        "to incorporate this story: Story 1. "
        "Do not use words. Be creative. "
        "Finally: Keep the man on the rooftop as he is "
        "and don't add any other people."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
        base_image_mime_type="image/jpeg",
    )
    [saved] = image_repository.add.call_args.args
    assert saved.prompt == expected_prompt
    assert saved.sensor_snapshot is snapshot
    assert saved.generated_at == mock_utc_now.return_value


@patch.object(
    ImageGenerationService, "_write_optimised_image", return_value=None
)
@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.utc_now")
def test_generate_and_save_image_uses_exact_stressed_prompt(
    mock_utc_now,
    _mock_random,
    _mock_write_optimised,
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
    image_repository = MagicMock()
    news_api_client = MagicMock()
    news_api_client.get_top_headlines = AsyncMock(return_value=["Story 1"])
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        image_repository=image_repository,
        news_api_client=news_api_client,
        open_meteo_client=_make_open_meteo_client_mock(),
        prompt_builder=ImagePromptBuilder(),
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    # 02:15 in Zurich
    mock_utc_now.return_value = datetime(
        2026, 4, 9, 0, 15, tzinfo=timezone.utc
    )
    expected_prompt = (
        "Use the provided painting as the base image: a Van Gogh-style "
        "view across Zurich rooftops towards the Uetliberg, with a "
        "potted plant on the rooftop ledge on the right. Keep the "
        "composition, the swirling brushwork and the TV tower on the "
        "hill. Edit the scene to reflect the plant's environment. "
        "Incorporate the following details about the plant's current state: "
        "#1: Make the potted plant wilt and its soil appear dry. "
        "#2: Leave the potted plant in deep shadow. "
        "#3: Add a cool, chilly atmosphere to the image. "
        "#4: Make the scene look like it's night. "
        "Incorporate the following information to update "
        "the sky and the hillside: "
        "#1: The current weather: clear sky. "
        "The temperature outside is 20.0°C. "
        "#2: Update the sky and the hillside "
        "to incorporate this story: Story 1. "
        "Do not use words. Be creative. "
        "Finally: Keep the man on the rooftop as he is "
        "and don't add any other people."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
        base_image_mime_type="image/jpeg",
    )
