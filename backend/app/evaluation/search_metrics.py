"""Métriques d'évaluation d'une recherche : fonctions pures.

Pour chaque question, on regarde à quel rang apparaît le premier morceau qui contient la
réponse attendue, puis on résume : rappel@k (la réponse est-elle dans les k premiers ?) et MRR
(moyenne de 1 / rang : récompense les réponses classées tôt).
"""

import unicodedata
from dataclasses import dataclass


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def first_relevant_rank(chunks: list[str], expected_phrase: str) -> int | None:
    """Rang (à partir de 1) du premier morceau contenant la phrase attendue, ou None."""
    wanted = _fold(expected_phrase)
    for rank, chunk in enumerate(chunks, start=1):
        if wanted in _fold(chunk):
            return rank
    return None


@dataclass(frozen=True)
class RetrievalSummary:
    questions: int
    recall: dict[int, float]  # k -> part des questions dont la réponse est dans les k premiers
    mrr: float


def summarize_ranks(ranks: list[int | None], ks: tuple[int, ...] = (1, 3, 5)) -> RetrievalSummary:
    if not ranks:
        raise ValueError("Il faut au moins une question pour résumer une recherche")
    total = len(ranks)
    return RetrievalSummary(
        questions=total,
        recall={k: sum(1 for r in ranks if r is not None and r <= k) / total for k in ks},
        mrr=sum(1 / r for r in ranks if r is not None) / total,
    )
