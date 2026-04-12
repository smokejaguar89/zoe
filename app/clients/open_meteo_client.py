from app.models.domain.weather_snapshot import WeatherSnapshot, WeatherCode
import requests


class OpenMeteoClientException(Exception):
    pass


class OpenMeteoClient:
    def __init__(self):
        self.ZURICH_LAT = 47.3769
        self.ZURICH_LON = 8.5417
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    def get_current_weather_zurich(self) -> WeatherSnapshot:
        FIELDS = [
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

        try:
            response = requests.get(
                self.api_url,
                params={
                    "latitude": self.ZURICH_LAT,
                    "longitude": self.ZURICH_LON,
                    "models": "meteoswiss_icon_ch1",
                    "current": ",".join(FIELDS),
                },
            )
        except requests.RequestException as e:
            raise OpenMeteoClientException(f"Error fetching weather data: {e}")

        if response.status_code != 200:
            raise OpenMeteoClientException(
                f"Error fetching weather data: {response.status_code}"
            )

        data = response.json()
        current = data.get("current", {})
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
            timestamp=data.get("current_time"),
        )
