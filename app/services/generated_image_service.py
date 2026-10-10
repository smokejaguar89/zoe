from pathlib import Path
from typing import Optional

from app.db.repositories.generated_image_repository import (
    GeneratedImageRepository,
)
from app.models.domain.generated_image import GeneratedImageMetadata

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
GENERATED_IMAGE_DIR = STATIC_DIR / "img" / "gemini"
OPTIMISED_IMAGE_DIR = STATIC_DIR / "img" / "gemini_optimised"


class GeneratedImageService:
    def __init__(self, image_repository: GeneratedImageRepository):
        self.image_repository = image_repository

    async def get_latest_generated_image(
        self,
    ) -> Optional[GeneratedImageMetadata]:
        return self.image_repository.get_latest()

    def generated_image_url_path(self, filename: str) -> str:
        return self._static_url_path(GENERATED_IMAGE_DIR / filename)

    def optimised_image_url_path(self, filename: str) -> str:
        return self._static_url_path(OPTIMISED_IMAGE_DIR / filename)

    def _static_url_path(self, path: Path) -> str:
        return f"/static/{path.relative_to(STATIC_DIR).as_posix()}"
