import requests
import os

from enum import Enum


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
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise NewsApiClientError("NEWS_API_KEY is not configured.")

    def get_top_headlines(
        self, category: NewsCategory = NewsCategory.GENERAL
    ) -> list[str]:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": category.value,
            "apiKey": self.api_key,
        }
        response = requests.get(url, params=params)
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
