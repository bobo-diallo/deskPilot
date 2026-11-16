from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    """Base commune des modèles SQLAlchemy."""


def build_engine(database_url: str) -> Engine:
    # Crée le dossier du fichier SQLite s'il n'existe pas encore.
    if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
        Path(database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url)


def init_database(engine: Engine) -> None:
    """Création simple des tables au démarrage (V1). Alembic viendra avec PostgreSQL."""
    # Import des modèles pour qu'ils soient enregistrés dans Base.metadata.
    from app.domains.conversations import models as _conversations  # noqa: F401
    from app.domains.documents import models as _documents  # noqa: F401
    from app.domains.llm import models as _llm  # noqa: F401

    Base.metadata.create_all(engine)


def get_session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session
