import asyncio
import threading
from unittest.mock import patch

from app.hardware.i2c_bus import I2CBus


def test_default_bus_is_created_on_the_i2c_thread() -> None:
    # Arrange
    created_on = []

    def fake_board_i2c():
        created_on.append(threading.current_thread().name)
        return "raw-bus"

    # Act
    with patch("app.hardware.i2c_bus.board.I2C", side_effect=fake_board_i2c):
        bus = I2CBus()

    # Assert
    assert bus.raw == "raw-bus"
    assert created_on[0].startswith("I2C_Thread")
    bus.shutdown()


def test_custom_bus_is_used_as_is() -> None:
    # Arrange
    custom_bus = object()

    # Act
    bus = I2CBus(bus=custom_bus)

    # Assert
    assert bus.raw is custom_bus
    bus.shutdown()


def test_run_executes_every_operation_on_one_thread() -> None:
    # Arrange
    bus = I2CBus(bus=object())

    async def scenario():
        return await asyncio.gather(
            *(
                bus.run(lambda: threading.current_thread().name)
                for _ in range(5)
            )
        )

    # Act
    thread_names = asyncio.run(scenario())

    # Assert
    assert len(set(thread_names)) == 1
    assert thread_names[0].startswith("I2C_Thread")
    assert thread_names[0] != threading.current_thread().name
    bus.shutdown()
