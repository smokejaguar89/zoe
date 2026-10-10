import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

import board

T = TypeVar("T")


class I2CBus:
    """Owns the Pi's I2C bus and runs every I2C operation on one dedicated
    thread, so reads from different sensors never interleave on the bus.

    Share a single instance between all I2C sensor drivers.
    """

    def __init__(self, bus=None):
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="I2C_Thread"
        )
        self.raw = self.run_sync(
            lambda: bus if bus is not None else board.I2C()
        )

    def run_sync(self, operation: Callable[[], T]) -> T:
        """Run on the I2C thread and wait for the result. For setup only."""
        return self._executor.submit(operation).result()

    async def run(self, operation: Callable[[], T]) -> T:
        """Run on the I2C thread without blocking the event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, operation)

    def shutdown(self):
        self._executor.shutdown(wait=True)
