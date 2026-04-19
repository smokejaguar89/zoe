from typing import Protocol


class ImageClient(Protocol):
    async def generate_image(
        self, prompt: str, base_image_bytes: bytes
    ) -> bytes: ...
