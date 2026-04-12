import os
import logging

from perigon import ApiClient, V1Api
import requests


class ApiException(Exception):
    pass


class PerigonClient:
    def __init__(self, api_key: str):
        self.api_key = api_key or os.getenv("PERIGON_API_KEY")
        logging.info(f"Perigon API key configured: {bool(self.api_key)}")
        if not self.api_key:
            logging.warning("PERIGON_API_KEY not set in environment")
        self.client = ApiClient(api_key=self.api_key) if self.api_key else None
        self.api = V1Api(self.client) if self.client else None

    def get_top_headlines(self) -> list[str]:
        url = "https://api.perigon.io/v1/stories/all"
        params = {
            "apiKey": self.api_key,
            "category": ["Politics"],
            "sortBy": "count",
            "from": "2026-04-09",
            "size": 10,
            "source": ["bbc.co.uk", "bbc.com", "cnn.com", "theguardian.com"],
        }

        # requests handles the repeated 'category' parameters correctly
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return []

        data = response.json()
        return [story["name"] for story in data.get("results", [])]
