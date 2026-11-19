from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class AgentRun(Base):
    """Une question posée à l'agent, avec tout ce qu'il faut pour la reprendre après une pause."""

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    # "running", "awaiting_approval", "completed" ou "step_limit"
    status: Mapped[str]
    answer: Mapped[str | None] = mapped_column(Text, default=None)
    model: Mapped[str]
    steps_used: Mapped[int] = mapped_column(default=0)  # nombre d'appels au modèle
    # Conversation complète (blocs bruts) : permet de reprendre l'agent là où il s'est arrêté.
    messages: Mapped[list] = mapped_column(JSON)
    # Appels d'outils pas encore traités (l'un d'eux attend peut-être l'approbation) et résultats
    # déjà obtenus pour le tour en cours.
    pending_calls: Mapped[list] = mapped_column(JSON, default=list)
    pending_results: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AgentStep(Base):
    """Un appel d'outil demandé par le modèle : la trace qui permet de comprendre l'agent."""

    __tablename__ = "agent_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"))
    position: Mapped[int]  # ordre dans l'exécution, à partir de 1
    tool_use_id: Mapped[str]
    tool_name: Mapped[str]
    arguments: Mapped[dict] = mapped_column(JSON)
    result: Mapped[str | None] = mapped_column(Text, default=None)
    # "executed", "error", "awaiting_approval" ou "rejected"
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
