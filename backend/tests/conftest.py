from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import init_database


@pytest.fixture
def session() -> Iterator[Session]:
    """Session sur une base SQLite en mémoire, neuve pour chaque test."""
    engine = create_engine("sqlite://")
    init_database(engine)
    with Session(engine) as db_session:
        yield db_session
