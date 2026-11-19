from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import init_database
from app.domains.search.ports import Embedder
from app.domains.search.service import SearchService
from app.evaluation.search_dataset import SearchDataset
from app.evaluation.search_metrics import first_relevant_rank

MODES = ("keyword", "vector", "hybrid")
# On regarde les 10 premiers morceaux : au-delà, un utilisateur (ou un agent) n'ira pas lire.
DEPTH = 10


@dataclass(frozen=True)
class QuestionResult:
    question_id: str
    tags: tuple[str, ...]
    rank: int | None  # rang du premier bon morceau, None s'il n'est pas dans les 10 premiers


def run_search_eval(dataset: SearchDataset, embedder: Embedder) -> dict[str, list[QuestionResult]]:
    """Indexe les contrats dans une base en mémoire, puis pose chaque question dans les 3 modes."""
    engine = create_engine("sqlite://")  # base jetable : l'évaluation ne touche pas la vraie base
    init_database(engine)
    with Session(engine) as session:
        service = SearchService(session, embedder)
        for document in dataset.documents:
            service.index_text(document.title, document.text)

        results: dict[str, list[QuestionResult]] = {}
        for mode in MODES:
            ranks = []
            for question in dataset.questions:
                hits = service.search(question.question, k=DEPTH, mode=mode)
                rank = first_relevant_rank(
                    [hit.text for hit in hits],
                    question.expected_phrase,
                    sources=[hit.title for hit in hits],
                    expected_source=question.expected_title,
                )
                ranks.append(QuestionResult(question.id, question.tags, rank))
            results[mode] = ranks
    return results
