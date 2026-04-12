import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.news_api_client import (
    NewsApiClient,
    NewsApiClientError,
    NewsCategory,
)


def test_news_api_client_raises_when_no_api_key() -> None:
    # Act / Assert
    with (
        patch("app.clients.news_api_client.os.getenv", return_value=None),
        pytest.raises(NewsApiClientError) as error,
    ):
        NewsApiClient(api_key=None)

    assert str(error.value) == "NEWS_API_KEY is not configured."


def test_get_top_headlines_returns_titles_for_200_response() -> None:
    # Arrange
    client = NewsApiClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "articles": [
            {"title": "Headline 1"},
            {"title": "Headline 2"},
        ]
    }
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    # Act
    with patch(
        "app.clients.news_api_client.httpx.AsyncClient"
    ) as MockAsyncClient:
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        headlines = asyncio.run(
            client.get_top_headlines(category=NewsCategory.SCIENCE)
        )

    # Assert
    assert headlines == ["Headline 1", "Headline 2"]
    mock_http_client.get.assert_called_once_with(
        "https://newsapi.org/v2/top-headlines",
        params={
            "category": "science",
            "apiKey": "test-key",
        },
    )


def test_get_top_headlines_raises_for_non_200_response() -> None:
    # Arrange
    client = NewsApiClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "rate limited"
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    # Act
    with patch(
        "app.clients.news_api_client.httpx.AsyncClient"
    ) as MockAsyncClient:
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(NewsApiClientError) as error:
            asyncio.run(
                client.get_top_headlines(category=NewsCategory.GENERAL)
            )

    # Assert
    assert (
        str(error.value)
        == "Error fetching top headlines: 429 - rate limited"
    )
