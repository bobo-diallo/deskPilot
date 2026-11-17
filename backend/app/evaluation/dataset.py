import json
from dataclasses import dataclass
from pathlib import Path

from app.domains.documents.file_types import detect_media_type
from app.domains.extraction.schemas import Invoice


@dataclass(frozen=True)
class DatasetCase:
    case_id: str
    path: Path
    media_type: str
    expected: Invoice  # vérité terrain
    tags: tuple[str, ...]


def load_dataset(directory: Path) -> list[DatasetCase]:
    """Charge les cas listés dans `manifest.json` (fichier, vérité attendue, étiquettes)."""
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    cases = []
    for entry in manifest["cases"]:
        path = directory / entry["file"]
        media_type = detect_media_type(path.read_bytes())
        if media_type is None:
            raise ValueError(f"Type de fichier non reconnu : {path}")
        expected = Invoice.model_validate_json(
            (directory / f"{entry['id']}.expected.json").read_text(encoding="utf-8")
        )
        cases.append(DatasetCase(entry["id"], path, media_type, expected, tuple(entry["tags"])))
    return cases
