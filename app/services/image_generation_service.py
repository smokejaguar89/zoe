import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional
from enum import Enum

from app.db.database import Database
from app.clients.client_protocols import ImageClient
from app.clients.news_api_client import NewsApiClient, NewsCategory
from app.clients.open_meteo_client import OpenMeteoClient
from app.models.domain.generated_image import GeneratedImageMetadata
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.models.domain.weather_snapshot import WeatherSnapshot
from app.services.sensor_service import (
    LIGHT_LOW_LUX_THRESHOLD,
    LIGHT_NORMAL_LUX_UPPER_THRESHOLD,
    MOISTURE_THRESHOLD,
    SensorService,
    TEMPERATURE_COMFORT_C_UPPER_THRESHOLD,
    TEMPERATURE_COOL_C_THRESHOLD,
)


logger = logging.getLogger(__name__)


class ImageGenerationServiceError(Exception):
    pass


class DayPhase(Enum):
    SUNRISE = "sunrise"
    DAY = "day"
    SUNSET = "sunset"
    NIGHT = "night"


@dataclass(frozen=True)
class _PromptContext:
    snapshot: SensorSnapshot
    weather: WeatherSnapshot
    top_story: str


class _ImagePromptBuilder:
    def build(
        self,
        now: datetime,
        context: _PromptContext,
    ) -> str:

        # Introduction
        prompt = [
            (
                "Use the provided sunflower painting as the base image. "
                "Edit the scene to reflect the plant's environment."
            )
        ]

        # Image interior
        prompt.append(
            "Incorporate the following details about "
            "the plant's current state:"
        )
        prompt.append("#1: " + self.build_moisture_prompt(context.snapshot))
        prompt.append("#2: " + self.build_light_prompt(context.snapshot))
        prompt.append("#3: " + self.build_temperature_prompt(context.snapshot))
        prompt.append("#4: " + self.build_time_of_day_prompt(context.weather))

        # Image exterior
        prompt.append(
            "Incorporate the following information to update "
            "the background landscape:"
        )

        prompt.append("#1: " + self.build_weather_overview(context.weather))
        prompt.append(
            "#2: Update the background landscape "
            f"to incorporate this story: {context.top_story}. "
            "Do not use words. Be creative."
        )

        # Conclusion
        prompt.append("Finally: Don't include any people in the image.")

        return " ".join(prompt)

    def build_moisture_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.moisture < MOISTURE_THRESHOLD:
            return "Make the sunflower wilt and the soil appear dry."

        return "Keep the sunflower healthy and the soil well hydrated."

    def build_light_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.light < LIGHT_LOW_LUX_THRESHOLD:
            return "Dim the scene to suggest a dark room."

        if snapshot.light < LIGHT_NORMAL_LUX_UPPER_THRESHOLD:
            return "Use soft, natural indoor lighting."

        return "Brighten the scene to suggest strong daylight."

    def build_temperature_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.temperature < TEMPERATURE_COOL_C_THRESHOLD:
            return "Add a cool, chilly atmosphere to the image."

        if snapshot.temperature <= TEMPERATURE_COMFORT_C_UPPER_THRESHOLD:
            return "Keep a neutral, comfortable atmosphere in the image."

        return "Add a warm, slightly hot atmosphere to the image."

    def build_weather_overview(self, weather: WeatherSnapshot) -> str:
        prompt = []
        prompt.append(
            f"The current weather: "
            f"{weather.weather_code.name.replace('_', ' ').lower()}."
        )
        prompt.append(f"The temperature outside is {weather.temperature}°C.")

        return " ".join(prompt)

    def build_time_of_day_prompt(
        self, weather_snapshot: WeatherSnapshot
    ) -> str:
        time_of_day = self._get_time_of_day(
            weather_snapshot.sunrise, weather_snapshot.sunset
        )
        return f"Make the scene look like it's {time_of_day.value}."

    def _get_time_of_day(
        self, sunrise: datetime, sunset: datetime
    ) -> DayPhase:
        hour = datetime.now().hour
        sunrise_hour = sunrise.hour
        sunset_hour = sunset.hour

        if sunrise_hour <= hour < sunrise_hour + 2:
            return DayPhase.SUNRISE
        elif sunrise_hour + 2 <= hour < sunset_hour:
            return DayPhase.DAY
        elif sunset_hour <= hour < sunset_hour + 2:
            return DayPhase.SUNSET
        else:
            return DayPhase.NIGHT


class ImageGenerationService:
    BASE_IMAGE_PATH = (
        Path(__file__).resolve().parents[1]
        / "static"
        / "img"
        / "sunflower_window_base.jpeg"
    )
    GENERATED_IMAGE_DIR = (
        Path(__file__).resolve().parents[1] / "static" / "img" / "gemini"
    )

    def __init__(
        self,
        sensor_service: SensorService,
        image_client: ImageClient,
        database: Database,
        news_api_client: NewsApiClient,
        open_meteo_client: OpenMeteoClient,
    ):
        self.sensor_service = sensor_service
        self.image_client = image_client
        self.database = database
        self.news_api_client = news_api_client
        self.open_meteo_client = open_meteo_client
        self.base_image_path = self.BASE_IMAGE_PATH
        self.generated_image_dir = self.GENERATED_IMAGE_DIR
        self._prompt_builder = _ImagePromptBuilder()

    async def generate_and_save_image(self) -> Path:
        snapshot, weather, top_story = await asyncio.gather(
            self.sensor_service.get_snapshot(),
            self.open_meteo_client.get_current_weather_zurich(),
            self._get_news_headline(),
        )
        prompt = self._prompt_builder.build(
            now=datetime.now(),
            context=_PromptContext(
                snapshot=snapshot,
                weather=weather,
                top_story=top_story,
            ),
        )
        base_image_bytes = self.base_image_path.read_bytes()
        image_bytes = await self.image_client.generate_image(
            prompt=prompt,
            base_image_bytes=base_image_bytes,
        )
        generated_at = datetime.now()
        output_path = self._write_generated_image(image_bytes, generated_at)
        await self.database.save_generated_image_metadata(
            filename=output_path.name,
            prompt=prompt,
            generated_at=generated_at,
            snapshot=snapshot,
        )
        return output_path

    async def get_latest_generated_image(
        self,
    ) -> Optional[GeneratedImageMetadata]:

        return await self.database.get_latest_generated_image_metadata()

    async def _get_news_headline(self) -> str:
        category = random.choice([NewsCategory.SCIENCE, NewsCategory.GENERAL])
        stories = await self.news_api_client.get_top_headlines(
            category=category
        )
        if stories:
            return stories[0]
        raise ImageGenerationServiceError(
            "No news stories available to include in prompt."
        )

    def _write_generated_image(
        self,
        image_bytes: bytes,
        generated_at: datetime,
    ) -> Path:
        self.generated_image_dir.mkdir(parents=True, exist_ok=True)
        filename = f"sunflower_{self._timestamp_to_string(generated_at)}.jpg"
        output_path = self.generated_image_dir / filename
        output_path.write_bytes(image_bytes)
        return output_path

    def _timestamp_to_string(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d:%H:%M")
