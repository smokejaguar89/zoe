"""App configuration and filesystem paths.

Settings come from environment variables, falling back to the .env file in
the project root. Paths are built from this file's location, so they don't
depend on the directory the app is started from.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
GENERATED_IMAGE_DIR = STATIC_DIR / "img" / "gemini"
OPTIMISED_IMAGE_DIR = STATIC_DIR / "img" / "gemini_optimised"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        # The .env file may hold variables for other tools
        extra="ignore",
    )

    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.1-flash-image-preview"
    news_api_key: Optional[str] = None
    database_path: Path = PROJECT_ROOT / "sensors.db"
    # SENSOR_MODE=TEST runs with fake sensors (e.g. on a laptop). TEST=1 is
    # an older way of saying the same thing.
    sensor_mode: str = ""
    test: bool = False

    @property
    def test_mode(self) -> bool:
        return self.sensor_mode.strip().upper() == "TEST" or self.test

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
