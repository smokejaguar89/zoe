import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.gemini_service import GeminiService, GeminiServiceError


def test_generate_image_returns_decoded_bytes() -> None:
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(
        return_value=SensorSnapshot(
            temperature=26.0,
            humidity=45.0,
            light=50.0,
            moisture=40.0,
            pressure=1008.0,
        )
    )
    service = GeminiService(sensor_service=sensor_service, api_key="test-key")
    service._read_base_image_bytes = MagicMock(return_value=b"base-image")

    response = MagicMock()
    response.parts = [
        MagicMock(
            inline_data=MagicMock(
                data=b"generated-image",
            )
        )
    ]

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = response

    with patch(
        "app.services.gemini_service.genai.Client",
        return_value=mock_client,
    ):
        image_bytes = asyncio.run(service._generate_image())

    assert image_bytes == b"generated-image"
    sensor_service.get_snapshot.assert_awaited_once_with()
    mock_client.models.generate_content.assert_called_once()


def test_generate_image_raises_when_no_api_key() -> None:
    service = GeminiService(sensor_service=MagicMock(), api_key=None)
    service.api_key = None

    try:
        asyncio.run(service._generate_image())
    except GeminiServiceError as error:
        assert str(error) == "GEMINI_API_KEY is not configured."
    else:
        raise AssertionError("Expected GeminiServiceError to be raised")


def test_generate_and_save_image_writes_expected_jpg_name(tmp_path) -> None:
    service = GeminiService(sensor_service=MagicMock(), api_key="test-key")
    service.generated_image_dir = tmp_path
    service._generate_image = AsyncMock(return_value=b"jpg-bytes")
    service._current_timestamp_string = MagicMock(
        return_value="2026-04-03:13:39"
    )

    output_path = asyncio.run(service.generate_and_save_image())

    assert output_path.name == "sunflower_2026-04-03:13:39.jpg"
    assert output_path.read_bytes() == b"jpg-bytes"


def test_get_or_generate_image_reuses_recent_image(tmp_path) -> None:
    service = GeminiService(sensor_service=MagicMock(), api_key="test-key")
    service.generated_image_dir = tmp_path
    recent_image = tmp_path / "sunflower_2026-04-03:13:39.jpg"
    recent_image.write_bytes(b"existing")
    service.generate_and_save_image = AsyncMock(
        return_value=tmp_path / "sunflower_new.jpg"
    )

    output_path = asyncio.run(
        service.get_or_generate_image(max_age_minutes=30)
    )

    assert output_path == recent_image
    service.generate_and_save_image.assert_not_awaited()


def test_get_or_generate_image_generates_when_image_is_stale(tmp_path) -> None:
    service = GeminiService(sensor_service=MagicMock(), api_key="test-key")
    service.generated_image_dir = tmp_path
    stale_image = tmp_path / "sunflower_2026-04-03:12:00.jpg"
    stale_image.write_bytes(b"old")
    two_hours_ago = time.time() - (2 * 60 * 60)
    os.utime(stale_image, (two_hours_ago, two_hours_ago))

    new_image = tmp_path / "sunflower_2026-04-03:13:39.jpg"
    service.generate_and_save_image = AsyncMock(return_value=new_image)

    output_path = asyncio.run(
        service.get_or_generate_image(max_age_minutes=30)
    )

    assert output_path == new_image
    service.generate_and_save_image.assert_awaited_once_with()
