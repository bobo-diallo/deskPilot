from collections.abc import Iterator

import anthropic
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domains.llm.ports import LLMProvider
from app.domains.llm.providers.anthropic import AnthropicProvider


def get_db_session(request: Request) -> Iterator[Session]:
    """Ouvre une session de base de données pour la durée d'une requête."""
    with Session(request.app.state.engine) as session:
        yield session


def get_llm_provider() -> LLMProvider:
    """Fournisseur LLM réel. Les tests le remplacent par un faux (dependency_overrides)."""
    api_key = get_settings().anthropic_api_key
    if not api_key:
        raise HTTPException(
            status_code=503, detail="ANTHROPIC_API_KEY n'est pas configurée dans .env"
        )
    return AnthropicProvider(anthropic.Anthropic(api_key=api_key))
