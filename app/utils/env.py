import os


def is_test_mode() -> bool:
    """True when running without sensors (e.g. on a laptop)."""
    sensor_mode = os.getenv("SENSOR_MODE", "").strip().upper()
    if sensor_mode == "TEST":
        return True

    test_flag = os.getenv("TEST", "").strip().lower()
    return test_flag in {"1", "true", "yes", "on"}
