import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.scheduler.scheduler import Scheduler


def test_collect_data_job_gets_and_saves_snapshot() -> None:
    # Arrange
    snapshot = {"temperature": 22.0}
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    database = MagicMock()
    database.save_snapshot = AsyncMock()
    image_generation_service = MagicMock()
    scheduler_service = Scheduler(
        sensor_service=sensor_service,
        database=database,
        image_generation_service=image_generation_service,
    )

    # Act
    asyncio.run(scheduler_service._collect_data_job())

    # Assert
    sensor_service.get_snapshot.assert_awaited_once_with()
    database.save_snapshot.assert_awaited_once_with(snapshot)


@patch("app.scheduler.scheduler.scheduler.start")
@patch("app.scheduler.scheduler.scheduler.add_job")
def test_start_adds_job_and_starts_scheduler(
    add_job,
    start,
) -> None:
    # Arrange
    image_generation_service = MagicMock()
    scheduler_service = Scheduler(
        sensor_service=MagicMock(),
        database=MagicMock(),
        image_generation_service=image_generation_service,
    )

    # Act
    scheduler_service.start()

    # Assert
    assert add_job.call_count == 2
    first_args, first_kwargs = add_job.call_args_list[0]
    assert first_args[0] == scheduler_service._run_collect_data_job
    assert first_args[1] == "interval"
    assert first_kwargs["minutes"] == 1
    second_args, second_kwargs = add_job.call_args_list[1]
    assert second_args[0] == scheduler_service._run_generate_image_job
    assert second_args[1] == "interval"
    assert second_kwargs["hours"] == 6
    start.assert_called_once()


@patch("app.scheduler.scheduler.scheduler.shutdown")
def test_stop_shuts_down_scheduler(shutdown) -> None:
    # Arrange
    scheduler_service = Scheduler(
        sensor_service=MagicMock(),
        database=MagicMock(),
        image_generation_service=MagicMock(),
    )

    # Act
    scheduler_service.stop()

    # Assert
    shutdown.assert_called_once()


def test_generate_image_job_always_generates_image() -> None:
    # Arrange
    image_generation_service = MagicMock()
    image_generation_service.generate_and_save_image = AsyncMock()
    scheduler_service = Scheduler(
        sensor_service=MagicMock(),
        database=MagicMock(),
        image_generation_service=image_generation_service,
    )

    # Act
    asyncio.run(scheduler_service._generate_image_job())

    # Assert
    image_generation_service.generate_and_save_image.assert_awaited_once_with()
