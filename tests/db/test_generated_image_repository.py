from datetime import datetime, timezone

import pytest

from app.db.repositories.generated_image_repository import (
    GeneratedImageRepository,
)
from app.models.domain.generated_image import GeneratedImageMetadata
from tests.db.helpers import make_snapshot


@pytest.fixture
def repository(database):
    return GeneratedImageRepository(engine=database.engine)


def _metadata(filename: str, hour: int) -> GeneratedImageMetadata:
    return GeneratedImageMetadata(
        filename=filename,
        generated_at=datetime(2026, 4, 9, hour, tzinfo=timezone.utc),
        prompt="A prompt",
        sensor_snapshot=make_snapshot(
            datetime(2026, 4, 9, hour, tzinfo=timezone.utc)
        ),
    )


def test_get_latest_returns_none_when_empty(repository) -> None:
    assert repository.get_latest() is None


def test_get_latest_returns_newest(repository) -> None:
    # Arrange: added out of order
    repository.add(_metadata("image_10.jpg", 10))
    repository.add(_metadata("image_6.jpg", 6))

    # Act
    latest = repository.get_latest()

    # Assert
    assert latest.filename == "image_10.jpg"
    assert latest.generated_at == datetime(2026, 4, 9, 10, tzinfo=timezone.utc)


def test_add_round_trips_prompt_and_snapshot(repository) -> None:
    # Arrange
    metadata = _metadata("image.jpg", 10)

    # Act
    repository.add(metadata)
    stored = repository.get_latest()

    # Assert
    assert stored == metadata
