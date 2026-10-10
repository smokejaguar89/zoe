from typing import Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.models.db.generated_image_entity import GeneratedImageEntity
from app.models.domain.generated_image import GeneratedImageMetadata


class GeneratedImageRepository:
    """Reads and writes generated image metadata. Only services should use
    this."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def add(self, metadata: GeneratedImageMetadata) -> None:
        with Session(self.engine) as session:
            session.add(
                GeneratedImageEntity.from_generated_image_metadata(metadata)
            )
            session.commit()

    def get_latest(self) -> Optional[GeneratedImageMetadata]:
        """The most recently generated image, or None if there are none."""
        with Session(self.engine) as session:
            statement = select(GeneratedImageEntity).order_by(
                GeneratedImageEntity.generated_at.desc()
            )
            entity = session.exec(statement).first()
            if entity is None:
                return None
            return entity.to_generated_image_metadata()
