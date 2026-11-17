"""Génère le jeu d'évaluation (factures fictives, valeurs attendues, manifeste).

Usage, depuis backend/ :  .venv/bin/python scripts/generate_eval_dataset.py
Reproductible : la graine est fixe, relancer donne exactement les mêmes fichiers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.render import write_dataset  # noqa: E402
from app.evaluation.synthetic import generate_cases  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "demo-data" / "eval"

if __name__ == "__main__":
    cases = generate_cases()
    write_dataset(cases, OUTPUT_DIR)
    print(f"{len(cases)} cas écrits dans {OUTPUT_DIR}")
