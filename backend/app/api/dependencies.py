from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

import anthropic
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domains.documents.storage import FileStorage
from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.ports import DocumentExtractor
from app.domains.llm.ports import LLMProvider
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.service import LLMService


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


def get_storage() -> FileStorage:
    return FileStorage(Path(get_settings().uploads_dir))


def get_extractor(
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    session: Annotated[Session, Depends(get_db_session)],
) -> DocumentExtractor:
    """Extracteur Claude branché sur le service LLM (donc sur le journal des coûts)."""
    return ClaudeExtractor(LLMService(provider, session))
