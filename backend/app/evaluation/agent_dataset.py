import json
from dataclasses import dataclass
from pathlib import Path

from app.evaluation.search_dataset import SearchDocument, load_search_dataset


@dataclass(frozen=True)
class WorldInvoice:
    supplier_name: str
    invoice_number: str | None
    issue_date: str
    currency: str
    subtotal: str
    tax_amount: str
    total: str
    status: str


@dataclass(frozen=True)
class AgentQuestion:
    id: str
    question: str
    tags: tuple[str, ...]
    must_use: tuple[str, ...]  # outils que l'agent doit avoir appelés
    must_not_use: tuple[str, ...]  # outils qu'il ne doit pas appeler
    # Chaque groupe est une liste d'alternatives : la réponse doit en contenir une par groupe.
    answer_contains: tuple[tuple[str, ...], ...]
    answer_must_not_contain: tuple[str, ...]
    expected_status: str  # "completed" ou "awaiting_approval"
    max_tool_calls: int | None


@dataclass(frozen=True)
class AgentDataset:
    documents: list[SearchDocument]  # contrats à indexer (dont un contrat piégé)
    invoices: list[WorldInvoice]  # factures déjà extraites, numérotées 1, 2, 3… dans l'ordre
    questions: list[AgentQuestion]


def load_agent_dataset(agent_dir: Path, contracts_dir: Path) -> AgentDataset:
    """Charge le monde de l'agent : les contrats du jeu de recherche, plus ceux de `agent_dir`."""
    agent_dir = Path(agent_dir)
    documents = list(load_search_dataset(contracts_dir).documents)
    for path in sorted((agent_dir / "documents").glob("*.md")):
        title_line, _, body = path.read_text(encoding="utf-8").partition("\n")
        documents.append(SearchDocument(title_line.removeprefix("# ").strip(), body.strip()))

    world = json.loads((agent_dir / "world.json").read_text(encoding="utf-8"))
    raw = json.loads((agent_dir / "questions.json").read_text(encoding="utf-8"))
    questions = [
        AgentQuestion(
            id=entry["id"],
            question=entry["question"],
            tags=tuple(entry["tags"]),
            must_use=tuple(entry["must_use"]),
            must_not_use=tuple(entry["must_not_use"]),
            answer_contains=tuple(tuple(group) for group in entry["answer_contains"]),
            answer_must_not_contain=tuple(entry["answer_must_not_contain"]),
            expected_status=entry["expected_status"],
            max_tool_calls=entry["max_tool_calls"],
        )
        for entry in raw["questions"]
    ]
    return AgentDataset(documents, [WorldInvoice(**i) for i in world["invoices"]], questions)
