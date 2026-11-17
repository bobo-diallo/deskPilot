"""Essai : convertit chaque facture du jeu d'évaluation en Markdown avec Docling.

Mesure le temps de conversion et le « rappel de texte » : parmi les valeurs attendues
(fournisseur, numéro, totaux), quelle part se retrouve dans le texte converti ?
Aucun appel à un LLM : l'essai ne coûte rien.
"""

import json
import re
import statistics
import time
from pathlib import Path

from docling.document_converter import DocumentConverter

DATA = Path("/data")
OUT = Path("/out")


def digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def recall_checks(expected: dict, markdown: str) -> dict[str, bool]:
    flat = " ".join(markdown.split()).casefold()
    only_digits = digits(markdown)
    checks = {
        "supplier": expected["supplier_name"].casefold() in flat,
        "total": digits(f"{float(expected['total']):.2f}") in only_digits,
        "subtotal": digits(f"{float(expected['subtotal']):.2f}") in only_digits,
    }
    if expected["invoice_number"]:
        checks["number"] = expected["invoice_number"].casefold() in flat
    return checks


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((DATA / "manifest.json").read_text())
    converter = DocumentConverter()  # télécharge les modèles au premier lancement

    rows = []
    for entry in manifest["cases"]:
        started = time.perf_counter()
        result = converter.convert(str(DATA / entry["file"]))
        markdown = result.document.export_to_markdown()
        seconds = time.perf_counter() - started

        (OUT / f"{entry['id']}.md").write_text(markdown, encoding="utf-8")
        expected = json.loads((DATA / f"{entry['id']}.expected.json").read_text())
        checks = recall_checks(expected, markdown)
        rows.append({"id": entry["id"], "tags": entry["tags"], "seconds": round(seconds, 1),
                     "checks": checks})
        print(entry["id"], f"{seconds:.1f}s", checks, flush=True)

    (OUT / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    scored = [ok for row in rows for ok in row["checks"].values()]
    print("temps médian par facture :", statistics.median(r["seconds"] for r in rows), "s")
    print("rappel de texte global :", round(sum(scored) / len(scored) * 100, 1), "%")


if __name__ == "__main__":
    main()
