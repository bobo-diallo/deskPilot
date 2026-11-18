from collections import defaultdict

# Constante standard de la fusion par rang réciproque (valeur du papier d'origine).
DEFAULT_K = 60


def reciprocal_rank_fusion(
    rankings: list[list[int]], k: int = DEFAULT_K
) -> list[tuple[int, float]]:
    """Fusionne plusieurs classements en un seul (RRF).

    Chaque élément reçoit 1 / (k + rang) de chaque liste où il apparaît, puis les scores
    s'additionnent. On fusionne des **rangs**, pas des scores : les notes de BM25 et de la
    similarité de vecteurs n'ont pas la même échelle et ne s'additionnent pas.
    """
    scores: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] += 1 / (k + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
