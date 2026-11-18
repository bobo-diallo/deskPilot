from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExtractionStatus(StrEnum):
    VALIDATED = "validated"  # les contrôles de cohérence passent
    NEEDS_REVIEW = "needs_review"  # au moins une anomalie : à relire par un humain
    # Décisions humaines (voir domains/review) :
    APPROVED = "approved"  # relue et jugée juste telle quelle
    CORRECTED = "corrected"  # relue et corrigée à la main
    REJECTED = "rejected"  # relue et écartée


def _now() -> datetime:
    return datetime.now(UTC)


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    document_type: Mapped[str]  # "invoice" pour l'instant
    status: Mapped[str]  # valeur de ExtractionStatus
    data: Mapped[dict] = mapped_column(JSON)  # champs extraits
    issues: Mapped[list] = mapped_column(JSON)  # anomalies détectées
    model: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
