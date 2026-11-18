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


def first_relevant_rank(
    chunks: list[str],
    expected_phrase: str,
    sources: list[str] | None = None,
    expected_source: str | None = None,
) -> int | None:
    """Rang (à partir de 1) du premier morceau pertinent, ou None.

    Un morceau est pertinent s'il contient la phrase attendue **et**, quand on le précise,
    s'il vient du bon document : une même phrase (« préavis d'un mois ») existe dans plusieurs
    contrats, et seul celui visé par la question est la bonne réponse.
    """
    wanted = _fold(expected_phrase)
    for rank, chunk in enumerate(chunks, start=1):
        if expected_source is not None and sources is not None:
            if sources[rank - 1] != expected_source:
                continue
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
