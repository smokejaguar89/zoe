from datetime import datetime, timezone

import httpx

from app.clients.http_retry import get_with_retries
from app.models.domain.weather_snapshot import WeatherSnapshot, WeatherCode
from app.utils.clock import LOCAL_TIMEZONE

# Enough of an error response to see why a request failed
MAX_ERROR_BODY_CHARS = 500


class OpenMeteoClientError(Exception):
    pass


class OpenMeteoClient:
    def __init__(self):
        self.ZURICH_LAT = 47.3769
        self.ZURICH_LON = 8.5417
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.REQUEST_TIMEOUT_SECONDS = 15.0
        self.MAX_ATTEMPTS = 3
        self.RETRY_DELAY_SECONDS = 1.0

    async def get_current_weather_zurich(self) -> WeatherSnapshot:
        CURRENT_FIELDS = [
            "wind_speed_10m",
            "temperature_2m",
            "is_day",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "cloud_cover",
        ]

        DAILY_FIELDS = [
            "sunrise",
            "sunset",
        ]

        try:
            response = await get_with_retries(
                self.api_url,
                params={
                    "latitude": self.ZURICH_LAT,
                    "longitude": self.ZURICH_LON,
                    "models": "meteoswiss_icon_ch1",
                    "current": ",".join(CURRENT_FIELDS),
                    "daily": ",".join(DAILY_FIELDS),
                    "timezone": LOCAL_TIMEZONE.key,
                },
                timeout_seconds=self.REQUEST_TIMEOUT_SECONDS,
                max_attempts=self.MAX_ATTEMPTS,
                retry_delay_seconds=self.RETRY_DELAY_SECONDS,
            )
        except httpx.RequestError as error:
            detail = str(error) or type(error).__name__
            raise OpenMeteoClientError(
                f"Error fetching weather data: {detail}"
            ) from error

        if response.status_code != 200:
            raise OpenMeteoClientError(
                f"Error fetching weather data: {response.status_code} - "
                f"{response.text[:MAX_ERROR_BODY_CHARS]}"
            )

        data = response.json()
        current = data.get("current", {})
        daily = data.get("daily", {})

        return WeatherSnapshot(
            weather_code=WeatherCode(current.get("weather_code")),
            wind_speed=current.get("wind_speed_10m"),
            temperature=current.get("temperature_2m"),
            is_day=bool(current.get("is_day")),
            precipitation=current.get("precipitation"),
            rain=current.get("rain"),
            showers=current.get("showers"),
            snowfall=current.get("snowfall"),
            cloud_cover=current.get("cloud_cover"),
            sunrise=self._parse_local_time(daily.get("sunrise", [])[0]),
            sunset=self._parse_local_time(daily.get("sunset", [])[0]),
            timestamp=self._parse_local_time(current.get("time")),
        )

    def _parse_local_time(self, value: str) -> datetime:
        # Open-Meteo returns naive times in the requested timezone
        return (
            datetime.fromisoformat(value)
            .replace(tzinfo=LOCAL_TIMEZONE)
            .astimezone(timezone.utc)
        )
