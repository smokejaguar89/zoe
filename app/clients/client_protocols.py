from typing import Protocol


class ImageClient(Protocol):
    async def generate_image(
        self, prompt: str, base_image_bytes: bytes, base_image_mime_type: str
    ) -> bytes: ...
