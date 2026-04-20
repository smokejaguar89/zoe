from typing import Protocol, TypeVar

try:
    from app.hardware.i2c_driver import I2CDriver
except NotImplementedError:
    # Fallback to fake driver when running on non-hardware platforms (e.g., macOS)
    from app.hardware.fake_drivers import FakeI2CDriver as I2CDriver  # type: ignore

ReadingT = TypeVar("ReadingT")


class HardwareDriverProtocol(Protocol[ReadingT]):
    """Protocol for I2C-based hardware drivers."""

    async def get_reading(self) -> ReadingT: ...

    # Note: this constructor shape is enforced by static type checking
    # tools (e.g., mypy/pyright), not at runtime.
    def __init__(self, i2c_driver: I2CDriver): ...
