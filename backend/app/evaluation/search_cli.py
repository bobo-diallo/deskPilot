"""Évaluation de la recherche : `python -m app.evaluation.search_cli`. Gratuit : aucun appel API."""

import argparse
import json
from datetime import date
from pathlib import Path

from app.domains.search.embedders.fake import FakeEmbedder
from app.domains.search.embedders.fastembed_embedder import FastEmbedEmbedder
from app.evaluation.search_dataset import load_search_dataset
from app.evaluation.search_report import render_search_report
from app.evaluation.search_runner import run_search_eval

REPO_ROOT = Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.evaluation.search_cli", description=__doc__
    )
    parser.add_argument("--embedder", choices=["fastembed", "fake"], default="fastembed")
    parser.add_argument("--dataset", type=Path, default=REPO_ROOT / "demo-data" / "search-eval")
    parser.add_argument("--report-dir", type=Path, default=REPO_ROOT / "docs" / "evaluation")
    parser.add_argument(
        "--raw-dir", type=Path, default=REPO_ROOT / "backend" / "data" / "evaluation"
    )
    parser.add_argument("--name", default="search")
    args = parser.parse_args(argv)

    embedder = FastEmbedEmbedder() if args.embedder == "fastembed" else FakeEmbedder()
    results = run_search_eval(load_search_dataset(args.dataset), embedder)

    today = date.today()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.report_dir / f"{today.isoformat()}-{args.name}.md"
    report_path.write_text(
        render_search_report(results, today, embedder.model_name), encoding="utf-8"
    )
    raw = {
        "embedder": embedder.model_name,
        "modes": {
            mode: [{"id": r.question_id, "tags": list(r.tags), "rank": r.rank} for r in rows]
            for mode, rows in results.items()
        },
    }
    (args.raw_dir / f"{args.name}.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"Terminé. Rapport : {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
