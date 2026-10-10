import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.api import _format_duration, router
from app.dependencies import get_generated_image_service
from app.models.domain.generated_image import GeneratedImageMetadata
from app.services.generated_image_service import GeneratedImageService

_NEXT_PULL_TIME = datetime(2026, 4, 9, 12, 10, tzinfo=timezone.utc)


@pytest.fixture
def image_service():
    """Real GeneratedImageService backed by a mocked repository."""
    return GeneratedImageService(image_repository=MagicMock())


@pytest.fixture
def app(image_service):
    """Create FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_generated_image_service] = lambda: (
        image_service
    )
    return app


@pytest.fixture
def client(app):
    """Create TestClient for the app."""
    with patch(
        "app.api.api.get_next_image_pull_time", return_value=_NEXT_PULL_TIME
    ):
        yield TestClient(app, base_url="http://zoe.local:8000")


def _set_latest_image(image_service, metadata):
    image_service.get_latest_generated_image = AsyncMock(return_value=metadata)


def _metadata(filename="test_image.jpg"):
    return GeneratedImageMetadata(
        filename=filename,
        generated_at=datetime(2026, 4, 9, 12, 0, tzinfo=timezone.utc),
    )


def test_eink_pull_returns_200_with_valid_image(client, image_service):
    # Arrange
    _set_latest_image(image_service, _metadata())

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {
        "status": 200,
        "type": "SHOW",
        "message": "Image retrieved successfully",
        "data": {
            "next_cron_time": "2026-04-09T12:10:00Z",
            "image_url": (
                "http://zoe.local:8000/static/img/gemini_optimised/"
                "test_image.jpg"
            ),
        },
    }


def test_eink_pull_calls_image_service(client, image_service):
    # Arrange
    _set_latest_image(image_service, _metadata())

    # Act
    client.get("/api/images/eink_pull")

    # Assert
    image_service.get_latest_generated_image.assert_awaited_once_with()


def test_eink_pull_without_image_still_returns_next_pull_time(
    client, image_service
):
    # Arrange
    _set_latest_image(image_service, None)

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "status": 200,
        "type": None,
        "message": "No image available",
        "data": {
            "next_cron_time": "2026-04-09T12:10:00Z",
            "image_url": None,
        },
    }


def test_eink_pull_only_accepts_get(client, image_service):
    # Arrange
    _set_latest_image(image_service, _metadata())

    # Act
    response = client.post("/api/images/eink_pull")

    # Assert
    assert response.status_code == 405


def test_eink_pull_logs_when_the_frame_will_next_request_an_image(
    client, image_service, caplog
) -> None:
    # Arrange: next pull is 12:10 UTC (14:10 in Zurich), now is 10:25 UTC
    _set_latest_image(image_service, _metadata())

    # Act
    with (
        patch(
            "app.api.api.utc_now",
            return_value=datetime(2026, 4, 9, 10, 25, tzinfo=timezone.utc),
        ),
        caplog.at_level(logging.INFO, logger="app.api.api"),
    ):
        client.get("/api/images/eink_pull")

    # Assert
    assert (
        "eInk frame will next request an image at 2026-04-09 14:10 CEST "
        "(in 1h 45m)."
    ) in caplog.text


def test_eink_pull_logs_next_request_even_without_an_image(
    client, image_service, caplog
) -> None:
    # Arrange
    _set_latest_image(image_service, None)

    # Act
    with caplog.at_level(logging.INFO, logger="app.api.api"):
        client.get("/api/images/eink_pull")

    # Assert
    assert "eInk frame will next request an image at 2026-04-09 14:10" in (
        caplog.text
    )


def test_format_duration() -> None:
    assert _format_duration(timedelta(minutes=9, seconds=40)) == "10m"
    assert _format_duration(timedelta(hours=3, minutes=5)) == "3h 05m"
    assert _format_duration(timedelta(minutes=-2)) == "0m"
