from typing import Protocol, TypeVar

from app.hardware.locked_i2c_bus import LockedI2CBus

ReadingT = TypeVar("ReadingT")


class ReadingDriver(Protocol[ReadingT]):
    def get_reading(self) -> ReadingT: ...


class LockedI2CBusDriver(ReadingDriver[ReadingT], Protocol[ReadingT]):
    # Note: this constructor shape is enforced by static type checking
    # tools (e.g., mypy/pyright), not at runtime.
    def __init__(self, i2c_bus: LockedI2CBus): ...
