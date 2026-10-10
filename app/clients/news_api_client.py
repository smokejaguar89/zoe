from enum import Enum
from typing import Optional

import httpx

from app.clients.http_retry import get_with_retries


class NewsApiClientError(Exception):
    pass


class NewsCategory(Enum):
    GENERAL = "general"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    SCIENCE = "science"
    SPORTS = "sports"
    TECHNOLOGY = "technology"


class NewsApiClient:
    REQUEST_TIMEOUT_SECONDS = 15.0
    MAX_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 1.0

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        if not self.api_key:
            raise NewsApiClientError("NEWS_API_KEY is not configured.")

    async def get_top_headlines(self, category: NewsCategory) -> list[str]:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": category.value,
            "apiKey": self.api_key,
        }
        try:
            response = await get_with_retries(
                url,
                params=params,
                timeout_seconds=self.REQUEST_TIMEOUT_SECONDS,
                max_attempts=self.MAX_ATTEMPTS,
                retry_delay_seconds=self.RETRY_DELAY_SECONDS,
            )
        except httpx.RequestError as error:
            detail = str(error) or type(error).__name__
            raise NewsApiClientError(
                f"Error fetching top headlines: {detail}"
            ) from error

        if response.status_code == 200:
            return [
                article["title"]
                for article in response.json().get("articles", [])
            ]
        else:
            raise NewsApiClientError(
                f"Error fetching top headlines: {response.status_code} - "
                f"{response.text}"
            )
