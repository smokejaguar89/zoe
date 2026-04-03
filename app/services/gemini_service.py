import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.params import Depends
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.sensor_service import (
    LIGHT_THRESHOLD,
    MOISTURE_THRESHOLD,
    SensorService,
    TEMPERATURE_THRESHOLD,
)

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-image-preview"


class GeminiServiceError(Exception):
    pass


class GeminiService:
    def __init__(
            self,
            sensor_service=Depends(SensorService),
            api_key: str | None = None,
            model: str = DEFAULT_GEMINI_MODEL):
        self.sensor_service = sensor_service
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
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
        image_bytes = await self._generate_image()
        self.generated_image_dir.mkdir(parents=True, exist_ok=True)
        filename = f"sunflower_{self._current_timestamp_string()}.jpg"
        output_path = self.generated_image_dir / filename
        output_path.write_bytes(image_bytes)
        return output_path

    async def get_or_generate_image(
            self,
            max_age_minutes: int = 30) -> Path:
        recent_image = self._get_most_recent_image(max_age_minutes)
        if recent_image is not None:
            return recent_image

        return await self.generate_and_save_image()

    async def _generate_image(self) -> bytes:
        if not self.api_key:
            raise GeminiServiceError("GEMINI_API_KEY is not configured.")

        prompt = await self._craft_image_prompt()
        client = genai.Client(api_key=self.api_key)
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=self._read_base_image_bytes(),
                        mime_type="image/jpeg",
                    ),
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
        except genai_errors.APIError as error:
            raise GeminiServiceError(
                "Gemini API request failed."
            ) from error
        image_bytes = self._extract_image_bytes(response)
        if image_bytes is None:
            raise GeminiServiceError(
                "Gemini response did not include an image."
            )

        return image_bytes

    async def _craft_image_prompt(self) -> str:
        snapshot: SensorSnapshot = await self.sensor_service.get_snapshot()

        prompt = [
            (
                "Use the provided sunflower painting as the base image. "
                "Edit the scene to reflect the plant's environment."
            )
        ]

        prompt.append("#1:")
        if snapshot.moisture < MOISTURE_THRESHOLD:
            prompt.append("Make the sunflower wilt and the soil appear dry.")
        else:
            prompt.append(
                "Keep the sunflower healthy and the soil well hydrated."
            )

        prompt.append("#2:")
        if snapshot.light < LIGHT_THRESHOLD:
            prompt.append("Dim the scene to suggest a dark room.")
        else:
            prompt.append("Brighten the scene to suggest strong daylight.")

        prompt.append("#3:")
        if snapshot.temperature < TEMPERATURE_THRESHOLD:
            prompt.append("Add a cool, chilly atmosphere to the image.")
        else:
            prompt.append("Add a warm, comfortable atmosphere to the image.")

        return " ".join(prompt)

    def _read_base_image_bytes(self) -> bytes:
        return self.base_image_path.read_bytes()

    def _current_timestamp_string(self) -> str:
        return datetime.now().strftime("%Y-%m-%d:%H:%M")

    def _get_most_recent_image(self, max_age_minutes: int) -> Path | None:
        if not self.generated_image_dir.exists():
            return None

        image_paths = list(self.generated_image_dir.glob("sunflower_*.jpg"))
        if not image_paths:
            return None

        newest_image = max(image_paths, key=lambda path: path.stat().st_mtime)
        newest_modified_at = datetime.fromtimestamp(
            newest_image.stat().st_mtime
        )
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        if newest_modified_at >= cutoff:
            return newest_image

        return None

    def _extract_image_bytes(self, response) -> bytes | None:
        parts = getattr(response, "parts", None)
        if parts:
            image_bytes = self._extract_image_bytes_from_parts(parts)
            if image_bytes is not None:
                return image_bytes

        candidates = getattr(response, "candidates", [])
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            image_bytes = self._extract_image_bytes_from_parts(parts)
            if image_bytes is not None:
                return image_bytes

        return None

    def _extract_image_bytes_from_parts(self, parts) -> bytes | None:
        for part in parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data is None:
                continue

            data = getattr(inline_data, "data", None)
            if isinstance(data, bytes):
                return data

        return None
