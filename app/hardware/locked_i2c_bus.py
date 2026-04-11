import threading
from _thread import LockType
from typing import Callable, TypeVar

import board

T = TypeVar("T")


class LockedI2CBus:
    """Shared I2C bus wrapper that serializes access with a lock."""

    def __init__(self, bus=None, lock: LockType | None = None):
        self.raw_bus = bus or board.I2C()
        self._lock = lock or threading.Lock()

    def run(self, operation: Callable[[], T]) -> T:
        with self._lock:
            return operation()
