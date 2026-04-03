import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.scheduler.scheduler import Scheduler


def test_collect_data_job_gets_and_saves_snapshot() -> None:
    snapshot = {"temperature": 22.0}
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    database = MagicMock()
    database.save_snapshot = AsyncMock()
    scheduler_service = Scheduler(
        sensor_service=sensor_service,
        database=database,
    )

    asyncio.run(scheduler_service._collect_data_job())

    sensor_service.get_snapshot.assert_awaited_once_with()
    database.save_snapshot.assert_awaited_once_with(snapshot)


@patch("app.scheduler.scheduler.scheduler.start")
@patch("app.scheduler.scheduler.scheduler.add_job")
def test_start_adds_job_and_starts_scheduler(
    add_job,
    start,
) -> None:
    scheduler_service = Scheduler(
        sensor_service=MagicMock(),
        database=MagicMock(),
    )

    scheduler_service.start()

    add_job.assert_called_once()
    args, kwargs = add_job.call_args
    assert args[0] == scheduler_service._run_collect_data_job
    assert args[1] == "interval"
    assert kwargs["minutes"] == 1
    start.assert_called_once()


@patch("app.scheduler.scheduler.scheduler.shutdown")
def test_stop_shuts_down_scheduler(shutdown) -> None:
    scheduler_service = Scheduler(
        sensor_service=MagicMock(),
        database=MagicMock(),
    )

    scheduler_service.stop()

    shutdown.assert_called_once()
