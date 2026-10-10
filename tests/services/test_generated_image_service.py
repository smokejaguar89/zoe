from unittest.mock import MagicMock
import asyncio

from app.services.generated_image_service import GeneratedImageService


def test_get_latest_generated_image_returns_repository_value() -> None:
    # Arrange
    expected = MagicMock()
    image_repository = MagicMock()
    image_repository.get_latest.return_value = expected
    service = GeneratedImageService(image_repository=image_repository)

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image is expected
    image_repository.get_latest.assert_called_once_with()


def test_get_latest_generated_image_returns_none_when_no_images() -> None:
    # Arrange
    image_repository = MagicMock()
    image_repository.get_latest.return_value = None
    service = GeneratedImageService(image_repository=image_repository)

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image is None


def test_image_url_paths_point_at_static_image_dirs() -> None:
    # Arrange
    service = GeneratedImageService(image_repository=MagicMock())

    # Act & Assert
    assert (
        service.generated_image_url_path("a.jpg") == "/static/img/gemini/a.jpg"
    )
    assert (
        service.optimised_image_url_path("a.jpg")
        == "/static/img/gemini_optimised/a.jpg"
    )
