import random
from datetime import datetime
import logging
from pathlib import Path
from typing import Protocol

from fastapi.params import Depends

from app.db.database import Database
from app.clients.gemini_client import GeminiClient
from app.models.domain.generated_image import GeneratedImage
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.sensor_service import (
    LIGHT_THRESHOLD,
    MOISTURE_THRESHOLD,
    SensorService,
    TEMPERATURE_THRESHOLD,
)


logger = logging.getLogger(__name__)


class ImageClient(Protocol):
    def generate_image(self, prompt: str, base_image_bytes: bytes) -> bytes:
        ...


class ImageGenerationService:
    def __init__(
            self,
            sensor_service: SensorService = Depends(SensorService),
            image_client: ImageClient = Depends(GeminiClient),
            database: Database = Depends(Database)):
        self.sensor_service = sensor_service
        self.image_client = image_client
        self.database = database
        self.base_image_path = (
            Path(__file__).resolve().parents[1]
            / "static"
            / "img"
            / "sunflower_base.jpg"
        )
        self.generated_image_dir = (
            Path(__file__).resolve().parents[1]
            / "static"
            / "img"
            / "gemini"
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
        filename = (
            f"sunflower_{self._timestamp_to_string(generated_at)}.jpg"
        )
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
        prompt = [
            (
                "Use the provided sunflower painting as the base image. "
                "Edit the scene to reflect the plant's environment."
            )
        ]

        prompt.append("#1:" + self._build_moisture_prompt(snapshot))
        prompt.append("#2:" + self._build_light_prompt(snapshot))
        prompt.append("#3:" + self._build_temperature_prompt(snapshot))
        prompt.append("#4:" + self._build_time_of_day_prompt(datetime.now()))

        if self._should_include_easter_egg():
            easter_egg_prompt = self._get_easter_egg_prompt().strip()
            if easter_egg_prompt:
                prompt.append("#5:" + easter_egg_prompt)

        special_event_prompt = self._maybe_get_special_event_prompt().strip()
        if special_event_prompt:
            prompt.append("#6:" + special_event_prompt)

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
        if snapshot.light < LIGHT_THRESHOLD:
            return "Dim the scene to suggest a dark room."

        return "Brighten the scene to suggest a bright room."

    def _build_temperature_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.temperature < TEMPERATURE_THRESHOLD:
            return "Add a cool, chilly atmosphere to the image."

        return "Add a warm, comfortable atmosphere to the image."

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
