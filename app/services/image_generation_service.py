import random
from datetime import datetime
import logging
from pathlib import Path
from typing import Protocol

from app.db.database import Database
from app.clients.news_api_client import NewsApiClient, NewsCategory
from app.clients.open_meteo_client import OpenMeteoClient
from app.models.domain.generated_image import GeneratedImage
from app.models.domain.sensor_snapshot import SensorSnapshot
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


class ImageClient(Protocol):
    def generate_image(
        self, prompt: str, base_image_bytes: bytes
    ) -> bytes: ...


class ImageGenerationService:
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
        self.base_image_path = (
            Path(__file__).resolve().parents[1]
            / "static"
            / "img"
            / "sunflower_window_base.jpeg"
        )
        self.generated_image_dir = (
            Path(__file__).resolve().parents[1] / "static" / "img" / "gemini"
        )

    async def generate_and_save_image(self) -> Path:
        snapshot = await self.sensor_service.get_snapshot()
        prompt = self._craft_image_prompt(snapshot)
        logger.info("Crafted image prompt: %s", prompt)
        image_bytes = self.image_client.generate_image(
            prompt=prompt,
            base_image_bytes=self.base_image_path.read_bytes(),
        )
        self.generated_image_dir.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now()
        filename = f"sunflower_{self._timestamp_to_string(generated_at)}.jpg"
        output_path = self.generated_image_dir / filename
        output_path.write_bytes(image_bytes)
        await self.database.save_generated_image(
            filename=filename,
            generated_at=generated_at,
            snapshot=snapshot,
        )
        return output_path

    async def get_latest_generated_image(self) -> GeneratedImage:
        return await self.database.get_latest_generated_image()

    def _craft_image_prompt(self, snapshot: SensorSnapshot) -> str:

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
        prompt.append("#1: " + self._build_moisture_prompt(snapshot))
        prompt.append("#2: " + self._build_light_prompt(snapshot))
        prompt.append("#3: " + self._build_temperature_prompt(snapshot))
        prompt.append("#4: " + self._build_time_of_day_prompt(datetime.now()))

        # Image exterior
        prompt.append(
            "Incorporate the following information to update "
            "the background landscape:"
        )

        weather_overview = self._get_weather_overview()
        prompt.append("#1: " + weather_overview)

        top_story = self._get_news_headline()
        prompt.append(
            "#2: Update the background landscape "
            f"to incorporate this story: {top_story}."
        )

        # Conclusion
        prompt.append("Finally: Don't include any people in the image.")

        return " ".join(prompt)

    def _get_news_headline(self) -> str:
        category = random.choice([NewsCategory.SCIENCE, NewsCategory.GENERAL])
        stories = self.news_api_client.get_top_headlines(category=category)
        if stories:
            return stories[0]
        raise ImageGenerationServiceError(
            "No news stories available to include in prompt."
        )

    def _get_weather_overview(self) -> str:
        weather = self.open_meteo_client.get_current_weather_zurich()
        prompt = []
        prompt.append(
            f"The current weather: "
            f"{weather.weather_code.name.replace('_', ' ').lower()}."
        )
        prompt.append(f"The temperature outside is {weather.temperature}°C.")
        return " ".join(prompt)

    def _should_include_easter_egg(self) -> bool:
        return random.random() < 0.25

    def _get_easter_egg_prompt(self) -> str:
        return ""

    def _maybe_get_special_event_prompt(self) -> str:
        month, day = datetime.now().month, datetime.now().day
        if month == 9 and day == 11:
            # TODO: something for Clara's birthday
            return ""
        if month == 8 and day == 22:
            # TODO: something for my birthday
            return ""
        # Add some more logic for... anniversary? christmas? easter?
        return ""

    def _build_moisture_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.moisture < MOISTURE_THRESHOLD:
            return "Make the sunflower wilt and the soil appear dry."

        return "Keep the sunflower healthy and the soil well hydrated."

    def _build_light_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.light < LIGHT_LOW_LUX_THRESHOLD:
            return "Dim the scene to suggest a dark room."

        if snapshot.light < LIGHT_NORMAL_LUX_UPPER_THRESHOLD:
            return "Use soft, natural indoor lighting."

        return "Brighten the scene to suggest strong daylight."

    def _build_temperature_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.temperature < TEMPERATURE_COOL_C_THRESHOLD:
            return "Add a cool, chilly atmosphere to the image."

        if snapshot.temperature <= TEMPERATURE_COMFORT_C_UPPER_THRESHOLD:
            return "Keep a neutral, comfortable atmosphere in the image."

        return "Add a warm, slightly hot atmosphere to the image."

    def _build_time_of_day_prompt(self, time: datetime) -> str:
        hour = time.hour
        if 5 <= hour < 12:
            return "Make the scene look like it's morning."
        elif 12 <= hour < 17:
            return "Make the scene look like it's afternoon."
        elif 17 <= hour < 21:
            return "Make the scene look like it's evening."
        else:
            return "Make the scene look like it's night."

    def _timestamp_to_string(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d:%H:%M")
