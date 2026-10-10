import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.db.database import EntityNotFoundError
from app.services.generated_image_service import GeneratedImageService


def test_get_latest_generated_image_returns_database_value() -> None:
    # Arrange
    expected = MagicMock()
    database = MagicMock()
    database.get_latest_generated_image_metadata = AsyncMock(
        return_value=expected
    )
    service = GeneratedImageService(database=database)

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image == expected
    database.get_latest_generated_image_metadata.assert_awaited_once_with()


def test_get_latest_generated_image_returns_none_when_database_empty() -> None:
    # Arrange
    database = MagicMock()
    database.get_latest_generated_image_metadata = AsyncMock(
        side_effect=EntityNotFoundError("No generated image found.")
    )
    service = GeneratedImageService(database=database)

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image is None


def test_image_url_paths_point_at_static_image_dirs() -> None:
    # Arrange
    service = GeneratedImageService(database=MagicMock())

    # Act & Assert
    assert (
        service.generated_image_url_path("a.jpg") == "/static/img/gemini/a.jpg"
    )
    assert (
        service.optimised_image_url_path("a.jpg")
        == "/static/img/gemini_optimised/a.jpg"
    )
