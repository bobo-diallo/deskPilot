from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChunkEmbedding(Base):
    """Vecteur d'un morceau, avec le nom du modèle qui l'a calculé.

    Les vecteurs de deux modèles différents ne sont pas comparables : on garde donc le nom du
    modèle et la recherche ignore les vecteurs d'un autre modèle.
    """

    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), primary_key=True)
    model: Mapped[str]
    vector: Mapped[list] = mapped_column(JSON)
