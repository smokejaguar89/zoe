from typing import Protocol, TypeVar

from app.hardware.i2c_driver import I2CDriver

ReadingT = TypeVar("ReadingT")


class ReadingDriver(Protocol[ReadingT]):
    async def get_reading(self) -> ReadingT: ...


class HardwareDriverProtocol(ReadingDriver[ReadingT], Protocol[ReadingT]):
    # Note: this constructor shape is enforced by static type checking
    # tools (e.g., mypy/pyright), not at runtime.
    def __init__(self, i2c_driver: I2CDriver): ...
