import asyncio
import mimetypes
import random
from datetime import datetime
import logging
from pathlib import Path
from PIL import Image

from app.db.repositories.generated_image_repository import (
    GeneratedImageRepository,
)
from app.clients.client_protocols import ImageClient
from app.clients.news_api_client import NewsApiClient, NewsCategory
from app.clients.open_meteo_client import OpenMeteoClient
from app.config import GENERATED_IMAGE_DIR, OPTIMISED_IMAGE_DIR, STATIC_DIR
from app.models.domain.generated_image import GeneratedImageMetadata
from app.services.sensor_service import SensorService
from app.utils.clock import to_local, utc_now
from app.utils.prompt_builder import ImagePromptBuilder, PromptContext


logger = logging.getLogger(__name__)


class ImageGenerationServiceError(Exception):
    pass


class ImageGenerationService:
    BASE_IMAGE_PATH = STATIC_DIR / "img" / "uetli_base.jpeg"
    BASE_IMAGE_MIME_TYPE, _ = mimetypes.guess_type(BASE_IMAGE_PATH.name)
    GENERATED_IMAGE_DIR = GENERATED_IMAGE_DIR
    OPTIMISED_IMAGE_DIR = OPTIMISED_IMAGE_DIR

    def __init__(
        self,
        sensor_service: SensorService,
        image_client: ImageClient,
        image_repository: GeneratedImageRepository,
        news_api_client: NewsApiClient,
        open_meteo_client: OpenMeteoClient,
        prompt_builder: ImagePromptBuilder,
    ):
        self.sensor_service = sensor_service
        self.image_client = image_client
        self.image_repository = image_repository
        self.news_api_client = news_api_client
        self.open_meteo_client = open_meteo_client
        self.prompt_builder = prompt_builder
        self.base_image_path = self.BASE_IMAGE_PATH
        self.generated_image_dir = self.GENERATED_IMAGE_DIR
        self.optimised_image_dir = self.OPTIMISED_IMAGE_DIR

    async def generate_and_save_image(self) -> Path:
        snapshot, weather, top_story = await asyncio.gather(
            self.sensor_service.get_snapshot(),
            self.open_meteo_client.get_current_weather_zurich(),
            self._get_news_headline(),
        )
        prompt = self.prompt_builder.build(
            now=utc_now(),
            context=PromptContext(
                snapshot=snapshot,
                weather=weather,
                top_story=top_story,
            ),
        )
        base_image_bytes = self.base_image_path.read_bytes()
        image_bytes = await self.image_client.generate_image(
            prompt=prompt,
            base_image_bytes=base_image_bytes,
            base_image_mime_type=self.BASE_IMAGE_MIME_TYPE,
        )
        generated_at = utc_now()
        output_path = self._write_generated_image(
            image_bytes, generated_at, self.generated_image_dir
        )
        # For e-ink display. Resizing is CPU-bound, so keep it off the event
        # loop that also serves API requests.
        await asyncio.to_thread(
            self._write_optimised_image,
            output_path,
            self.optimised_image_dir / output_path.name,
        )
        self.image_repository.add(
            GeneratedImageMetadata(
                filename=output_path.name,
                generated_at=generated_at,
                prompt=prompt,
                sensor_snapshot=snapshot,
            )
        )
        return output_path

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
        self, image_bytes: bytes, generated_at: datetime, path: Path
    ) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        timestamp = self._timestamp_to_string(to_local(generated_at))
        filename = f"sunflower_{timestamp}_P.jpg"
        output_path = path / filename
        output_path.write_bytes(image_bytes)
        return output_path

    def _write_optimised_image(
        self, input_path: Path, output_path: Path
    ) -> Path:
        TARGET_RES = (1200, 1600)
        with Image.open(input_path) as img:
            # Resize down slightly first
            img = img.resize(TARGET_RES, Image.Resampling.LANCZOS)
            img.save(output_path, "JPEG", quality=70, optimize=True)
        return output_path

    def _timestamp_to_string(self, value: datetime) -> str:
        return value.strftime("%Y_%m_%d_%H_%M")
