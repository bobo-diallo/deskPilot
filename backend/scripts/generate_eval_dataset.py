"""Génère le jeu d'évaluation (factures fictives, valeurs attendues, manifeste).

Usage, depuis backend/ :  .venv/bin/python scripts/generate_eval_dataset.py
Jeu de validation indépendant : ... --seed 7 --out data/eval-holdout
Reproductible : à graine égale, relancer donne exactement les mêmes fichiers.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.render import write_dataset  # noqa: E402
from app.evaluation.synthetic import generate_cases  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "demo-data" / "eval"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    cases = generate_cases(seed=args.seed)
    write_dataset(cases, args.out)
    print(f"{len(cases)} cas (graine {args.seed}) écrits dans {args.out}")
