"""Fixtures for tests that run against a real SQLite database."""

import pytest

from app.db.database import Database


@pytest.fixture
def database(tmp_path):
    database = Database(url=f"sqlite:///{tmp_path / 'test.db'}")
    database.init()
    return database
