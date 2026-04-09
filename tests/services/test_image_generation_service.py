import asyncio
from datetime import datetime
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.image_generation_service import ImageGenerationService


def test_generate_and_save_image_writes_expected_jpg_name(tmp_path) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
    )
    service.generated_image_dir = tmp_path
    service.base_image_path = tmp_path / "sunflower_base.jpg"
    service.base_image_path.write_bytes(b"base-image")
    service._craft_image_prompt = MagicMock(return_value="plant prompt")
    service._timestamp_to_string = MagicMock(
        return_value="2026-04-03:13:39"
    )

    # Act
    output_path = asyncio.run(service.generate_and_save_image())

    # Assert
    assert output_path.name == "sunflower_2026-04-03:13:39.jpg"
    assert output_path.read_bytes() == b"jpg-bytes"
    image_client.generate_image.assert_called_once_with(
        prompt="plant prompt",
        base_image_bytes=b"base-image",
    )
    database.save_generated_image.assert_awaited_once_with(
        filename="sunflower_2026-04-03:13:39.jpg",
        generated_at=ANY,
        snapshot=snapshot,
    )


def test_get_latest_generated_image_returns_database_value() -> None:
    # Arrange
    expected = MagicMock()
    database = MagicMock()
    database.get_latest_generated_image = AsyncMock(return_value=expected)
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=database,
    )

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image == expected
    database.get_latest_generated_image.assert_awaited_once_with()


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_generate_and_save_image_uses_exact_healthy_prompt(
    mock_datetime,
    _mock_random,
) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "#1:Keep the sunflower healthy and the soil well hydrated. "
        "#2:Brighten the scene to suggest a bright room. "
        "#3:Add a warm, comfortable atmosphere to the image. "
        "#4:Make the scene look like it's afternoon."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_generate_and_save_image_uses_exact_stressed_prompt(
    mock_datetime,
    _mock_random,
) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=18.0,
        humidity=45.0,
        light=12.0,
        moisture=10.0,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 2, 15)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "#1:Make the sunflower wilt and the soil appear dry. "
        "#2:Dim the scene to suggest a dark room. "
        "#3:Add a cool, chilly atmosphere to the image. "
        "#4:Make the scene look like it's night."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


@patch("app.services.image_generation_service.random.random", return_value=0.1)
@patch("app.services.image_generation_service.datetime")
def test_generate_and_save_image_includes_easter_egg_prompt_when_enabled(
    mock_datetime,
    _mock_random,
) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    service._get_easter_egg_prompt = MagicMock(
        return_value="Add a tiny ladybug on a leaf."
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "#1:Keep the sunflower healthy and the soil well hydrated. "
        "#2:Brighten the scene to suggest a bright room. "
        "#3:Add a warm, comfortable atmosphere to the image. "
        "#4:Make the scene look like it's afternoon. "
        "#5:Add a tiny ladybug on a leaf."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


@patch("app.services.image_generation_service.random.random", return_value=0.9)
@patch("app.services.image_generation_service.datetime")
def test_generate_and_save_image_includes_special_event_prompt_when_present(
    mock_datetime,
    _mock_random,
) -> None:
    # Arrange
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
    )
    service.generated_image_dir = MagicMock()
    service.generated_image_dir.mkdir = MagicMock()
    service.generated_image_dir.__truediv__ = MagicMock(
        return_value=MagicMock(write_bytes=MagicMock())
    )
    service.base_image_path = MagicMock(
        read_bytes=MagicMock(return_value=b"base")
    )
    service._maybe_get_special_event_prompt = MagicMock(
        return_value="Add soft lanterns in the background."
    )
    mock_datetime.now.return_value = datetime(2026, 4, 9, 14, 30)
    expected_prompt = (
        "Use the provided sunflower painting as the base image. "
        "Edit the scene to reflect the plant's environment. "
        "#1:Keep the sunflower healthy and the soil well hydrated. "
        "#2:Brighten the scene to suggest a bright room. "
        "#3:Add a warm, comfortable atmosphere to the image. "
        "#4:Make the scene look like it's afternoon. "
        "#6:Add soft lanterns in the background."
    )

    # Act
    asyncio.run(service.generate_and_save_image())

    # Assert
    image_client.generate_image.assert_called_once_with(
        prompt=expected_prompt,
        base_image_bytes=b"base",
    )


def test_get_latest_generated_image_returns_none_when_database_empty() -> None:
    # Arrange
    database = MagicMock()
    database.get_latest_generated_image = AsyncMock(return_value=None)
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=database,
    )

    # Act
    generated_image = asyncio.run(service.get_latest_generated_image())

    # Assert
    assert generated_image is None
    database.get_latest_generated_image.assert_awaited_once_with()
