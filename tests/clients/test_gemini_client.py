from unittest.mock import MagicMock, patch

import pytest

from app.clients.gemini_client import GeminiClient, GeminiClientError


def test_generate_image_returns_decoded_bytes() -> None:
    # Arrange
    client = GeminiClient(api_key="test-key")
    response = MagicMock()
    response.parts = [
        MagicMock(
            inline_data=MagicMock(
                data=b"generated-image",
            )
        )
    ]
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = response

    # Act
    with patch(
        "app.clients.gemini_client.genai.Client",
        return_value=mock_genai_client,
    ):
        image_bytes = client.generate_image(
            prompt="generate a sunflower",
            base_image_bytes=b"base-image",
        )

    # Assert
    assert image_bytes == b"generated-image"
    mock_genai_client.models.generate_content.assert_called_once()


def test_generate_image_raises_when_no_api_key() -> None:
    # Arrange
    client = GeminiClient(api_key=None)
    client.api_key = None

    # Act
    with pytest.raises(GeminiClientError) as error:
        client.generate_image(
            prompt="generate a sunflower",
            base_image_bytes=b"base-image",
        )

    # Assert
    assert str(error.value) == "GEMINI_API_KEY is not configured."
