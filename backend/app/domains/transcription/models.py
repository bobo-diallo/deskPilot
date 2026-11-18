from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Transcription(Base):
    """Texte transcrit d'un enregistrement, rattaché à l'extraction qu'il a nourrie."""

    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_id: Mapped[int] = mapped_column(ForeignKey("extractions.id"))
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str]
    duration_seconds: Mapped[float]
    model: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
