import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.dependencies import get_apscheduler
from app.scheduler.scheduler import (
    MAX_IMAGE_GENERATION_ATTEMPTS,
    Scheduler,
    get_next_image_pull_time,
)
from app.utils.clock import utc_now


def _make_scheduler(image_generation_service=None, apscheduler=None):
    return Scheduler(
        sensor_service=MagicMock(),
        image_generation_service=image_generation_service or MagicMock(),
        scheduler=apscheduler or MagicMock(),
    )


def _failing_image_generation_service() -> MagicMock:
    image_generation_service = MagicMock()
    image_generation_service.generate_and_save_image = AsyncMock(
        side_effect=Exception("boom")
    )
    return image_generation_service


def test_collect_data_job_records_a_snapshot() -> None:
    # Arrange
    sensor_service = MagicMock()
    sensor_service.record_snapshot = AsyncMock()
    scheduler_service = Scheduler(
        sensor_service=sensor_service,
        image_generation_service=MagicMock(),
        scheduler=MagicMock(),
    )

    # Act
    asyncio.run(scheduler_service._collect_data_job())

    # Assert
    sensor_service.record_snapshot.assert_awaited_once_with()


def test_start_adds_jobs_and_starts_scheduler() -> None:
    # Arrange
    apscheduler = MagicMock()
    scheduler_service = _make_scheduler(apscheduler=apscheduler)

    # Act
    scheduler_service.start()

    # Assert
    assert apscheduler.add_job.call_count == 2
    first_args, first_kwargs = apscheduler.add_job.call_args_list[0]
    assert first_args[0] == scheduler_service._collect_data_job
    assert first_args[1] == "interval"
    assert first_kwargs["minutes"] == 15

    second_args, second_kwargs = apscheduler.add_job.call_args_list[1]
    assert second_args[0] == scheduler_service._generate_image_job
    assert second_args[1] == "cron"
    assert second_kwargs["hour"] == "6,10,14,18,22"
    assert second_kwargs["minute"] == 0
    apscheduler.start.assert_called_once_with()


def test_generate_image_job_schedules_retry_on_failure() -> None:
    # Arrange
    apscheduler = MagicMock()
    scheduler_service = _make_scheduler(
        _failing_image_generation_service(), apscheduler
    )

    # Act
    asyncio.run(scheduler_service._generate_image_job())

    # Assert
    apscheduler.add_job.assert_called_once()
    args, kwargs = apscheduler.add_job.call_args
    assert args[0] == scheduler_service._generate_image_job
    assert args[1] == "date"
    assert kwargs["run_date"].tzinfo == timezone.utc
    assert kwargs["kwargs"] == {"attempt": 2}
    assert kwargs["id"] == "generate_image_retry"
    assert kwargs["replace_existing"] is True


def test_generate_image_job_gives_up_after_max_attempts() -> None:
    # Arrange
    apscheduler = MagicMock()
    image_generation_service = _failing_image_generation_service()
    scheduler_service = _make_scheduler(image_generation_service, apscheduler)

    # Act
    asyncio.run(
        scheduler_service._generate_image_job(
            attempt=MAX_IMAGE_GENERATION_ATTEMPTS
        )
    )

    # Assert
    image_generation_service.generate_and_save_image.assert_awaited_once()
    apscheduler.add_job.assert_not_called()


def test_generate_image_job_does_not_schedule_retry_on_success() -> None:
    # Arrange
    apscheduler = MagicMock()
    image_generation_service = MagicMock()
    image_generation_service.generate_and_save_image = AsyncMock()
    scheduler_service = _make_scheduler(image_generation_service, apscheduler)

    # Act
    asyncio.run(scheduler_service._generate_image_job())

    # Assert
    image_generation_service.generate_and_save_image.assert_awaited_once_with()
    apscheduler.add_job.assert_not_called()


def test_stop_shuts_down_scheduler() -> None:
    # Arrange
    apscheduler = MagicMock()
    scheduler_service = _make_scheduler(apscheduler=apscheduler)

    # Act
    scheduler_service.stop()

    # Assert
    apscheduler.shutdown.assert_called_once_with(wait=False)


def test_jobs_run_on_the_apps_event_loop() -> None:
    """Jobs must share the API's loop so asyncio locks in drivers work."""

    async def scenario():
        job_loops = []

        async def record_snapshot():
            job_loops.append(asyncio.get_running_loop())

        sensor_service = MagicMock()
        sensor_service.record_snapshot = record_snapshot
        # The real AsyncIOScheduler the app uses, not a mock
        scheduler_service = Scheduler(
            sensor_service=sensor_service,
            image_generation_service=MagicMock(),
            scheduler=get_apscheduler(),
        )
        scheduler_service.start()
        scheduler_service._scheduler.add_job(
            scheduler_service._collect_data_job, "date", run_date=utc_now()
        )
        for _ in range(50):
            if job_loops:
                break
            await asyncio.sleep(0.05)
        scheduler_service.stop()
        return asyncio.get_running_loop(), job_loops

    # Act
    loop, job_loops = asyncio.run(scenario())

    # Assert
    assert job_loops == [loop]


def test_next_image_pull_time_is_next_slot_today() -> None:
    # 09:00 in Zurich (CEST, UTC+2)
    now = datetime(2026, 4, 9, 7, 0, tzinfo=timezone.utc)

    assert get_next_image_pull_time(now) == datetime(
        2026, 4, 9, 8, 10, tzinfo=timezone.utc
    )


def test_next_image_pull_time_rolls_over_to_tomorrow() -> None:
    # 23:00 in Zurich (CEST, UTC+2)
    now = datetime(2026, 4, 9, 21, 0, tzinfo=timezone.utc)

    assert get_next_image_pull_time(now) == datetime(
        2026, 4, 10, 4, 10, tzinfo=timezone.utc
    )


def test_next_image_pull_time_respects_dst_change() -> None:
    # 23:00 on 24 Oct (CEST, UTC+2); clocks go back overnight to CET, UTC+1
    now = datetime(2026, 10, 24, 21, 0, tzinfo=timezone.utc)

    assert get_next_image_pull_time(now) == datetime(
        2026, 10, 25, 5, 10, tzinfo=timezone.utc
    )
