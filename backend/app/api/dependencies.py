from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import anthropic
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domains.agent.service import AgentService
from app.domains.agent.tools.base import ToolRegistry
from app.domains.agent.tools.invoices import (
    CheckInvoiceTool,
    ExportInvoicesTool,
    ListInvoicesTool,
)
from app.domains.agent.tools.search import SearchDocumentsTool
from app.domains.documents.storage import FileStorage
from app.domains.extraction.extractors.audio import AudioExtractor
from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.extractors.dispatch import MediaTypeExtractor
from app.domains.extraction.ports import DocumentExtractor
from app.domains.llm.ports import LLMProvider
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.router import Task, choose_model
from app.domains.llm.service import LLMService
from app.domains.search.embedders.fastembed_embedder import FastEmbedEmbedder
from app.domains.search.ports import Embedder
from app.domains.search.service import SearchService
from app.domains.transcription.ports import Transcriber
from app.domains.transcription.transcribers.faster_whisper import FasterWhisperTranscriber


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


@lru_cache
def _whisper_transcriber(model_size: str) -> FasterWhisperTranscriber:
    # Mis en cache : le modèle Whisper se charge une seule fois, pas à chaque requête
    return FasterWhisperTranscriber(model_size)


def get_transcriber() -> Transcriber:
    """Transcripteur Whisper local. Les tests le remplacent par un faux."""
    return _whisper_transcriber(get_settings().whisper_model_size)


def get_extractor(
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    session: Annotated[Session, Depends(get_db_session)],
    transcriber: Annotated[Transcriber, Depends(get_transcriber)],
) -> DocumentExtractor:
    """Extracteurs Claude branchés sur le service LLM (donc sur le journal des coûts)."""
    llm_service = LLMService(provider, session)
    return MediaTypeExtractor(
        visual=ClaudeExtractor(llm_service),
        audio=AudioExtractor(transcriber, llm_service),
    )


@lru_cache
def _fastembed_embedder() -> FastEmbedEmbedder:
    # Mis en cache : le modèle (0,22 Go) se charge une seule fois, pas à chaque requête
    return FastEmbedEmbedder()


def get_embedder() -> Embedder:
    """Embeddings locaux. Les tests le remplacent par un faux."""
    return _fastembed_embedder()


def get_agent_service(
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    session: Annotated[Session, Depends(get_db_session)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
) -> AgentService:
    """L'agent et ses quatre outils, branchés sur le service LLM (donc sur le journal des coûts)."""
    registry = ToolRegistry(
        [
            SearchDocumentsTool(SearchService(session, embedder)),
            ListInvoicesTool(session),
            CheckInvoiceTool(session),
            ExportInvoicesTool(session, Path(get_settings().exports_dir)),
        ]
    )
    return AgentService(
        LLMService(provider, session), registry, session, model=choose_model(Task.AGENT)
    )
