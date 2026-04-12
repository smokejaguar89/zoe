import os

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-image-preview"


class GeminiClientError(Exception):
    pass


class GeminiClient:
    def __init__(
        self, api_key: str | None = None, model: str = DEFAULT_GEMINI_MODEL
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model

    def generate_image(self, prompt: str, base_image_bytes: bytes) -> bytes:
        if not self.api_key:
            raise GeminiClientError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=self.api_key)
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=base_image_bytes,
                        mime_type="image/png",
                    ),
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
        except genai_errors.APIError as error:
            raise GeminiClientError("Gemini API request failed.") from error

        image_bytes = self._extract_image_bytes(response)
        if image_bytes is None:
            raise GeminiClientError(
                "Gemini response did not include an image."
            )

        return image_bytes

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
