import asyncio
import logging
from types import SimpleNamespace
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
    client = GeminiClient(api_key="test-key", model="test-model")
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
                base_image_mime_type="image/jpeg",
            )
        )

    # Assert
    assert image_bytes == b"generated-image"
    mock_genai_client.aio.models.generate_content.assert_called_once()


def test_generate_image_retries_on_empty_response() -> None:
    # Arrange
    client = GeminiClient(api_key="test-key", model="test-model")
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
                base_image_mime_type="image/jpeg",
            )
        )

    # Assert
    assert image_bytes == b"retry-image"
    assert mock_genai_client.aio.models.generate_content.call_count == 2


def test_generate_image_raises_after_max_attempts() -> None:
    # Arrange
    client = GeminiClient(api_key="test-key", model="test-model")
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
                    base_image_mime_type="image/jpeg",
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
    client = GeminiClient(api_key=None, model="test-model")

    # Act
    with pytest.raises(GeminiClientError) as error:
        asyncio.run(
            client.generate_image(
                prompt="generate a sunflower",
                base_image_bytes=b"base-image",
                base_image_mime_type="image/jpeg",
            )
        )

    # Assert
    assert str(error.value) == "GEMINI_API_KEY is not configured."


def _generate(client, response, prompt="generate a sunflower"):
    mock_genai_client = MagicMock()
    mock_genai_client.aio.models.generate_content = AsyncMock(
        return_value=response
    )
    with patch(
        "app.clients.gemini_client.genai.Client",
        return_value=mock_genai_client,
    ):
        image_bytes = asyncio.run(
            client.generate_image(
                prompt=prompt,
                base_image_bytes=b"base-image",
                base_image_mime_type="image/jpeg",
            )
        )
    return image_bytes, mock_genai_client.aio.models.generate_content


def test_generate_image_sends_base_image_with_its_mime_type() -> None:
    # Act
    _, generate_content = _generate(
        GeminiClient(api_key="test-key", model="test-model"),
        _make_response_with_image(),
    )

    # Assert
    base_image_part = generate_content.call_args.kwargs["contents"][1]
    assert base_image_part.inline_data.mime_type == "image/jpeg"
    assert base_image_part.inline_data.data == b"base-image"


def test_generate_image_does_not_log_image_data(caplog) -> None:
    # Arrange: a response whose repr includes the image bytes
    image_data = b"IMAGE-BYTES" * 100
    response = SimpleNamespace(
        parts=[SimpleNamespace(inline_data=SimpleNamespace(data=image_data))],
        candidates=[
            SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))
        ],
    )

    # Act
    with caplog.at_level(logging.DEBUG, logger="app.clients.gemini_client"):
        _generate(
            GeminiClient(api_key="test-key", model="test-model"), response
        )

    # Assert
    assert "IMAGE-BYTES" not in caplog.text
    assert "Gemini returned an image (1100 bytes, finish_reason=STOP)" in (
        caplog.text
    )
    assert "Generating image with prompt: generate a sunflower" in caplog.text


def test_generate_image_logs_text_reply_when_no_image(caplog) -> None:
    # Arrange: Gemini answered with text instead of an image
    text_reply = SimpleNamespace(
        parts=None,
        candidates=[
            SimpleNamespace(
                finish_reason=SimpleNamespace(name="STOP"),
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            text="I can't edit this image.", inline_data=None
                        )
                    ]
                ),
            )
        ],
    )

    # Act
    with caplog.at_level(logging.WARNING, logger="app.clients.gemini_client"):
        with pytest.raises(GeminiClientError):
            _generate(
                GeminiClient(api_key="test-key", model="test-model"),
                text_reply,
            )

    # Assert
    assert "finish_reason=STOP" in caplog.text
    assert "I can't edit this image." in caplog.text
