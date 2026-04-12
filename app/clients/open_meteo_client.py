from datetime import datetime

import httpx
from app.models.domain.weather_snapshot import WeatherSnapshot, WeatherCode


class OpenMeteoClientError(Exception):
    pass


class OpenMeteoClient:
    def __init__(self):
        self.ZURICH_LAT = 47.3769
        self.ZURICH_LON = 8.5417
        self.api_url = "https://api.open-meteo.com/v1/forecast"

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
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    params={
                        "latitude": self.ZURICH_LAT,
                        "longitude": self.ZURICH_LON,
                        "models": "meteoswiss_icon_ch1",
                        "current": ",".join(CURRENT_FIELDS),
                        "daily": ",".join(DAILY_FIELDS),
                        "timezone": "Europe/Zurich",
                    },
                )
        except httpx.RequestError as e:
            detail = str(e) or type(e).__name__
            raise OpenMeteoClientError(
                f"Error fetching weather data: {detail}"
            )

        if response.status_code != 200:
            raise OpenMeteoClientError(
                f"Error fetching weather data: {response.status_code}"
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
            sunrise=datetime.fromisoformat(daily.get("sunrise", [])[0]),
            sunset=datetime.fromisoformat(daily.get("sunset", [])[0]),
            timestamp=datetime.fromisoformat(current.get("time")),
        )
