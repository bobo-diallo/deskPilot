from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchHit:
    """Un morceau de document retrouvé, avec sa source et sa note."""

    chunk_id: int
    document_id: int
    title: str
    text: str
    score: float


class DocumentSearch(Protocol):
    """Contrat de la recherche dans les documents : une question en entrée, des morceaux en sortie.

    L'agent ne connaît que ce contrat. L'implémentation du dépôt (SearchService) peut être
    remplacée par un autre mini-RAG sans toucher à l'agent.
    """

    def search(self, query: str, k: int = 5) -> list[SearchHit]: ...


class Embedder(Protocol):
    """Contrat d'un modèle d'embeddings : du texte en entrée, un vecteur de nombres par texte."""

    model_name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...
