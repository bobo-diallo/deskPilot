"""Génère le jeu d'évaluation audio : 12 factures dictées (voix de synthèse macOS).

Usage, depuis backend/ :  .venv/bin/python scripts/generate_eval_audio.py
Nécessite macOS (commande `say`) et ffmpeg. Même graine, même texte, mêmes conditions.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.audio_render import write_audio_dataset  # noqa: E402
from app.evaluation.synthetic import generate_cases  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "demo-data" / "eval-audio"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    write_audio_dataset(generate_cases(seed=args.seed), args.out, count=args.count)
    print(f"{args.count} dictées (graine {args.seed}) écrites dans {args.out}")
