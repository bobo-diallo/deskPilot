"""Évaluation de l'agent : `python -m app.evaluation.agent_cli --models haiku,sonnet --yes`.

Estime d'abord le coût et ne dépense rien sans `--yes` (appels réels au modèle).
"""

import argparse
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

from app.domains.llm.ports import LLMProvider
from app.domains.llm.pricing import compute_cost_usd
from app.domains.search.embedders.fake import FakeEmbedder
from app.domains.search.embedders.fastembed_embedder import FastEmbedEmbedder
from app.evaluation.agent_dataset import load_agent_dataset
from app.evaluation.agent_report import render_agent_report
from app.evaluation.agent_runner import run_agent_variant
from app.evaluation.cli import _default_provider

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
# Estimation grossière par question : 3 appels au modèle (outil, outil, réponse). À recaler sur
# la première mesure réelle, comme pour les autres évaluations.
CALLS_PER_QUESTION = 3
ESTIMATED_INPUT_TOKENS = 3_000
ESTIMATED_OUTPUT_TOKENS = 600


def main(
    argv: list[str] | None = None, provider_factory: Callable[[], LLMProvider] | None = None
) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.evaluation.agent_cli", description=__doc__)
    parser.add_argument("--models", default="haiku,sonnet")
    parser.add_argument("--runs", type=int, default=2, help="répétitions par question")
    parser.add_argument("--limit", type=int, help="ne garder que les N premières questions")
    parser.add_argument(
        "--tags", help="ne garder que les questions portant l'une de ces étiquettes"
    )
    parser.add_argument("--embedder", choices=["fastembed", "fake"], default="fastembed")
    parser.add_argument("--name", default="agent")
    parser.add_argument("--dataset-dir", type=Path, default=REPO_ROOT / "demo-data" / "agent-eval")
    parser.add_argument(
        "--contracts-dir", type=Path, default=REPO_ROOT / "demo-data" / "search-eval"
    )
    parser.add_argument("--report-dir", type=Path, default=REPO_ROOT / "docs" / "evaluation")
    parser.add_argument(
        "--raw-dir", type=Path, default=REPO_ROOT / "backend" / "data" / "evaluation"
    )
    parser.add_argument("--yes", action="store_true", help="confirme la dépense")
    args = parser.parse_args(argv)

    names = [name.strip() for name in args.models.split(",") if name.strip()]
    unknown = [name for name in names if name not in MODELS]
    if unknown:
        print(f"Modèle inconnu : {', '.join(unknown)}. Choix : {', '.join(MODELS)}")
        return 2

    dataset = load_agent_dataset(args.dataset_dir, args.contracts_dir)
    questions = dataset.questions
    if args.tags:
        wanted = {tag.strip() for tag in args.tags.split(",")}
        questions = [q for q in questions if wanted & set(q.tags)]
    if args.limit:
        questions = questions[: args.limit]

    trials = len(questions) * args.runs
    estimate = sum(
        trials
        * CALLS_PER_QUESTION
        * compute_cost_usd(MODELS[name], ESTIMATED_INPUT_TOKENS, ESTIMATED_OUTPUT_TOKENS)
        for name in names
    )
    print(
        f"Estimation : {trials * len(names)} essais ({len(questions)} questions x {args.runs} "
        f"répétitions x {len(names)} modèle(s)), environ {estimate:.2f} $".replace(".", ",")
    )
    if not args.yes:
        print("Rien n'a été dépensé. Relancer avec --yes pour exécuter.")
        return 1

    provider = (provider_factory or _default_provider)()
    embedder = FastEmbedEmbedder() if args.embedder == "fastembed" else FakeEmbedder()
    variants = []
    for name in names:
        print(f"Modèle {name} ({MODELS[name]})…")
        variants.append(
            run_agent_variant(name, MODELS[name], provider, dataset, embedder, args.runs, questions)
        )

    today = date.today()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.report_dir / f"{today.isoformat()}-{args.name}.md"
    report_path.write_text(
        render_agent_report({v.name: v.trials for v in variants}, today, MODELS), encoding="utf-8"
    )
    raw = {
        "variants": [
            {
                "name": v.name,
                "model": v.model,
                "trials": [
                    {
                        "question_id": t.question_id,
                        "run": t.run,
                        "tags": list(t.tags),
                        "success": t.success,
                        "failures": t.failures,
                        "unsafe": t.unsafe,
                        "tools": t.tools,
                        "steps_used": t.steps_used,
                        "status": t.status,
                        "answer": t.answer,
                        "cost_usd": t.cost_usd,
                        "input_tokens": t.input_tokens,
                        "output_tokens": t.output_tokens,
                        "latency_ms": t.latency_ms,
                        "error": t.error,
                    }
                    for t in v.trials
                ],
            }
            for v in variants
        ]
    }
    (args.raw_dir / f"{args.name}.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    spent = sum(t.cost_usd for v in variants for t in v.trials)
    spent_text = f"{spent:.4f} $".replace(".", ",")
    print(f"Terminé. Coût réel : {spent_text}. Rapport : {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
