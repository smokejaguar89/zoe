from pathlib import Path

import pytest

from app.config import PROJECT_ROOT, STATIC_DIR, TEMPLATES_DIR, Settings


@pytest.fixture
def clean_env(monkeypatch):
    for name in (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "NEWS_API_KEY",
        "DATABASE_PATH",
        "SENSOR_MODE",
        "TEST",
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults_without_env_or_env_file(clean_env) -> None:
    # Act
    settings = Settings(_env_file=None)

    # Assert
    assert settings.gemini_api_key is None
    assert settings.news_api_key is None
    assert settings.database_path == PROJECT_ROOT / "sensors.db"
    assert settings.test_mode is False


def test_reads_env_file(clean_env, tmp_path) -> None:
    # Arrange
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEY=gemini-key\nNEWS_API_KEY=news-key\nOTHER_TOOL=x\n"
    )

    # Act
    settings = Settings(_env_file=env_file)

    # Assert
    assert settings.gemini_api_key == "gemini-key"
    assert settings.news_api_key == "news-key"


def test_environment_variables_override_env_file(
    clean_env, monkeypatch, tmp_path
) -> None:
    # Arrange
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_MODEL=from-file\n")
    monkeypatch.setenv("GEMINI_MODEL", "from-env")

    # Act
    settings = Settings(_env_file=env_file)

    # Assert
    assert settings.gemini_model == "from-env"


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"SENSOR_MODE": "TEST"}, True),
        ({"SENSOR_MODE": "test"}, True),
        ({"TEST": "1"}, True),
        ({"TEST": "yes"}, True),
        ({"SENSOR_MODE": ""}, False),
        ({"TEST": "false"}, False),
    ],
)
def test_test_mode(clean_env, monkeypatch, env, expected) -> None:
    # Arrange
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    # Act & Assert
    assert Settings(_env_file=None).test_mode is expected


def test_paths_do_not_depend_on_working_directory(
    clean_env, monkeypatch, tmp_path
) -> None:
    # Arrange: start from somewhere else, as a systemd service might
    monkeypatch.chdir(tmp_path)

    # Act
    settings = Settings(_env_file=None)

    # Assert
    assert settings.database_url == f"sqlite:///{PROJECT_ROOT / 'sensors.db'}"
    assert STATIC_DIR.is_absolute() and STATIC_DIR.is_dir()
    assert TEMPLATES_DIR.is_absolute() and TEMPLATES_DIR.is_dir()


def test_database_path_can_be_overridden(clean_env, monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("DATABASE_PATH", "/data/zoe/sensors.db")

    # Act
    settings = Settings(_env_file=None)

    # Assert
    assert settings.database_path == Path("/data/zoe/sensors.db")
    assert settings.database_url == "sqlite:////data/zoe/sensors.db"
