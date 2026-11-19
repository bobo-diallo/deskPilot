import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchDocument:
    title: str
    text: str


@dataclass(frozen=True)
class SearchQuestion:
    id: str
    question: str
    expected_title: str  # contrat qui contient la réponse
    expected_phrase: str  # extrait qui doit se trouver dans le morceau retrouvé
    tags: tuple[str, ...]


@dataclass(frozen=True)
class SearchDataset:
    documents: list[SearchDocument]
    questions: list[SearchQuestion]


def load_search_dataset(directory: Path) -> SearchDataset:
    """Charge `documents/*.md` (première ligne « # Titre », puis le texte) et `questions.json`."""
    directory = Path(directory)
    documents = []
    for path in sorted((directory / "documents").glob("*.md")):
        title_line, _, body = path.read_text(encoding="utf-8").partition("\n")
        documents.append(SearchDocument(title_line.removeprefix("# ").strip(), body.strip()))
    raw = json.loads((directory / "questions.json").read_text(encoding="utf-8"))
    questions = [
        SearchQuestion(
            entry["id"],
            entry["question"],
            entry["expected_title"],
            entry["expected_phrase"],
            tuple(entry["tags"]),
        )
        for entry in raw["questions"]
    ]
    return SearchDataset(documents, questions)
