import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.gemini_client import (
    GeminiClient,
    GeminiClientError,
    MAX_ATTEMPTS,
)


def _make_response_with_image(data: bytes = b"generated-image") -> MagicMock:
    response = MagicMock()
    response.parts = [MagicMock(inline_data=MagicMock(data=data))]
    return response


def _make_empty_response() -> MagicMock:
    response = MagicMock()
    response.parts = None
    response.candidates = []
    return response


def test_generate_image_returns_decoded_bytes() -> None:
    # Arrange
    client = GeminiClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_genai_client.aio.models.generate_content = AsyncMock(
        return_value=_make_response_with_image()
    )

    # Act
    with patch(
        "app.clients.gemini_client.genai.Client",
        return_value=mock_genai_client,
    ):
        image_bytes = asyncio.run(
            client.generate_image(
                prompt="generate a sunflower",
                base_image_bytes=b"base-image",
            )
        )

    # Assert
    assert image_bytes == b"generated-image"
    mock_genai_client.aio.models.generate_content.assert_called_once()


def test_generate_image_retries_on_empty_response() -> None:
    # Arrange
    client = GeminiClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_genai_client.aio.models.generate_content = AsyncMock(
        side_effect=[
            _make_empty_response(),
            _make_response_with_image(b"retry-image"),
        ]
    )

    # Act
    with patch(
        "app.clients.gemini_client.genai.Client",
        return_value=mock_genai_client,
    ):
        image_bytes = asyncio.run(
            client.generate_image(
                prompt="generate a sunflower",
                base_image_bytes=b"base-image",
            )
        )

    # Assert
    assert image_bytes == b"retry-image"
    assert mock_genai_client.aio.models.generate_content.call_count == 2


def test_generate_image_raises_after_max_attempts() -> None:
    # Arrange
    client = GeminiClient(api_key="test-key")
    mock_genai_client = MagicMock()
    mock_genai_client.aio.models.generate_content = AsyncMock(
        return_value=_make_empty_response()
    )

    # Act
    with patch(
        "app.clients.gemini_client.genai.Client",
        return_value=mock_genai_client,
    ):
        with pytest.raises(GeminiClientError) as error:
            asyncio.run(
                client.generate_image(
                    prompt="generate a sunflower",
                    base_image_bytes=b"base-image",
                )
            )

    # Assert
    assert str(error.value) == "Gemini response did not include an image."
    assert (
        mock_genai_client.aio.models.generate_content.call_count
        == MAX_ATTEMPTS
    )


def test_generate_image_raises_when_no_api_key() -> None:
    # Arrange
    client = GeminiClient(api_key=None)
    client.api_key = None

    # Act
    with pytest.raises(GeminiClientError) as error:
        asyncio.run(
            client.generate_image(
                prompt="generate a sunflower",
                base_image_bytes=b"base-image",
            )
        )

    # Assert
    assert str(error.value) == "GEMINI_API_KEY is not configured."
