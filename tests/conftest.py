import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Provide lightweight stubs for hardware-specific modules so tests can run on
# non-Raspberry Pi / non-I2C CI environments.
if "board" not in sys.modules:
    board_module = types.ModuleType("board")
    board_module.I2C = lambda: object()
    sys.modules["board"] = board_module

if "adafruit_bme280" not in sys.modules:
    adafruit_bme280_module = types.ModuleType("adafruit_bme280")
    adafruit_bme280_basic_module = types.ModuleType("adafruit_bme280.basic")

    class _StubBME280:
        def __init__(self, *args, **kwargs):
            self.temperature = 0.0
            self.relative_humidity = 0.0
            self.pressure = 0.0

    adafruit_bme280_basic_module.Adafruit_BME280_I2C = _StubBME280
    adafruit_bme280_module.basic = adafruit_bme280_basic_module

    sys.modules["adafruit_bme280"] = adafruit_bme280_module
    sys.modules["adafruit_bme280.basic"] = adafruit_bme280_basic_module

if "adafruit_tsl2591" not in sys.modules:
    adafruit_tsl2591_module = types.ModuleType("adafruit_tsl2591")

    class _StubTSL2591:
        def __init__(self, *args, **kwargs):
            self.lux = 0.0

    adafruit_tsl2591_module.TSL2591 = _StubTSL2591
    sys.modules["adafruit_tsl2591"] = adafruit_tsl2591_module
