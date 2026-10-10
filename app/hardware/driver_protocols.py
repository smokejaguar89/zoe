from typing import Protocol, TypeVar

ReadingT = TypeVar("ReadingT", covariant=True)


class HardwareDriverProtocol(Protocol[ReadingT]):
    """Anything that can take a sensor reading: real or fake drivers.

    How a driver is constructed (I2C bus, GPIO pins, nothing at all for
    fakes) is up to the driver and wired in app/dependencies.py.
    """

    async def get_reading(self) -> ReadingT: ...
