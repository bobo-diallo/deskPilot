from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class ReviewDecision(Base):
    """Piste d'audit : ce qu'un humain a décidé, et ce que le système avait lu avant.

    On ne modifie jamais une ligne : une décision est un fait daté.
    """

    __tablename__ = "review_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_id: Mapped[int] = mapped_column(ForeignKey("extractions.id"))
    decision: Mapped[str]  # "approved", "corrected" ou "rejected"
    before: Mapped[dict] = mapped_column(JSON)  # données telles que le système les avait extraites
    after: Mapped[dict | None] = mapped_column(
        JSON, default=None
    )  # données corrigées, le cas échéant
    changed_fields: Mapped[list] = mapped_column(JSON)  # champs que l'humain a modifiés
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
