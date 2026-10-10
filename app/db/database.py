from datetime import datetime, timezone
import logging

from sqlalchemy import text
from sqlmodel import SQLModel, create_engine

# Imported so their tables are registered with SQLModel.metadata before
# create_all runs
from app.models.db.generated_image_entity import (  # noqa: F401
    GeneratedImageEntity,
)
from app.models.db.sensor_snapshot_entity import (  # noqa: F401
    SensorSnapshotEntity,
)

logger = logging.getLogger(__name__)

# Bump when adding a migration to _run_migrations
SCHEMA_VERSION = 1
# Format SQLAlchemy uses to store datetimes in SQLite
_SQLITE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class Database:
    """Owns the engine and the schema. Reading and writing data happens in
    the repositories in app/db/repositories."""

    def __init__(self, url: str):
        self.engine = create_engine(url)

    def init(self):
        SQLModel.metadata.create_all(self.engine)
        self._ensure_generated_image_prompt_column()
        self._run_migrations()

    def _run_migrations(self):
        with self.engine.begin() as connection:
            version = connection.exec_driver_sql(
                "PRAGMA user_version"
            ).scalar()
            if version >= SCHEMA_VERSION:
                return
            if version < 1:
                self._convert_generated_at_to_utc(connection)
            connection.exec_driver_sql(
                f"PRAGMA user_version = {SCHEMA_VERSION}"
            )

    def _convert_generated_at_to_utc(self, connection):
        # generated_at used to be written with naive datetime.now(), i.e. the
        # system's local time. Sensor timestamps were already UTC.
        rows = connection.exec_driver_sql(
            "SELECT id, generated_at FROM generatedimageentity"
        ).fetchall()
        for row_id, generated_at in rows:
            # astimezone() on a naive datetime assumes system local time
            utc = (
                datetime.fromisoformat(generated_at)
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )
            connection.exec_driver_sql(
                "UPDATE generatedimageentity "
                "SET generated_at = ? WHERE id = ?",
                (utc.strftime(_SQLITE_DATETIME_FORMAT), row_id),
            )
        logger.info("Converted %d generated_at values to UTC.", len(rows))

    def _ensure_generated_image_prompt_column(self):
        with self.engine.begin() as connection:
            columns = connection.exec_driver_sql(
                "PRAGMA table_info(generatedimageentity)"
            ).fetchall()
            column_names = {column[1] for column in columns}
            if "prompt" not in column_names:
                connection.execute(
                    text(
                        "ALTER TABLE generatedimageentity "
                        "ADD COLUMN prompt TEXT"
                    )
                )
