"""Commande d'évaluation : `python -m app.evaluation --variants sonnet-vision,haiku-vision --yes`.

Elle estime d'abord le coût et ne dépense rien sans `--yes`.
"""

import argparse
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings
from app.core.database import init_database
from app.domains.llm.ports import LLMProvider
from app.domains.llm.pricing import compute_cost_usd
from app.domains.llm.providers.factory import build_llm_provider
from app.domains.llm.service import LLMService
from app.evaluation.dataset import load_dataset
from app.evaluation.report import render_markdown
from app.evaluation.runner import VariantResult, run_variant
from app.evaluation.variants import VARIANTS

REPO_ROOT = Path(__file__).resolve().parents[3]


def _default_provider() -> LLMProvider:
    settings = Settings(_env_file=REPO_ROOT / ".env")
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY est absente (variable d'environnement ou .env)")
    return build_llm_provider(settings)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.evaluation", description=__doc__)
    parser.add_argument("--variants", default="sonnet-vision,haiku-vision")
    parser.add_argument("--runs", type=int, default=3, help="répétitions par facture")
    parser.add_argument("--limit", type=int, help="ne garder que les N premiers cas")
    parser.add_argument("--tags", help="ne garder que les cas portant l'une de ces étiquettes")
    parser.add_argument("--name", default="evaluation", help="nom du rapport")
    parser.add_argument("--dataset", type=Path, default=REPO_ROOT / "demo-data" / "eval")
    parser.add_argument("--report-dir", type=Path, default=REPO_ROOT / "docs" / "evaluation")
    parser.add_argument(
        "--raw-dir", type=Path, default=REPO_ROOT / "backend" / "data" / "evaluation"
    )
    parser.add_argument("--yes", action="store_true", help="confirme la dépense")
    return parser


def _raw_results(results: list[VariantResult]) -> dict:
    return {
        "variants": [
            {
                "name": result.name,
                "trials": [
                    {
                        "case_id": t.case_id,
                        "run": t.run,
                        "tags": list(t.tags),
                        "model": t.model,
                        "input_tokens": t.input_tokens,
                        "output_tokens": t.output_tokens,
                        "cost_usd": t.cost_usd,
                        "latency_ms": t.latency_ms,
                        "error": t.error,
                        "status": t.score.status,
                        "failed": t.score.failed,
                        "hallucinations": t.score.hallucinations,
                        "fields": t.score.fields,
                    }
                    for t in result.trials
                ],
            }
            for result in results
        ]
    }


def main(
    argv: list[str] | None = None, provider_factory: Callable[[], LLMProvider] | None = None
) -> int:
    args = _parser().parse_args(argv)

    names = [name.strip() for name in args.variants.split(",") if name.strip()]
    unknown = [name for name in names if name not in VARIANTS]
    if unknown:
        print(f"Variante inconnue : {', '.join(unknown)}. Choix : {', '.join(VARIANTS)}")
        return 2

    cases = load_dataset(args.dataset)
    if args.tags:
        wanted = {tag.strip() for tag in args.tags.split(",")}
        cases = [case for case in cases if wanted & set(case.tags)]
    if args.limit:
        cases = cases[: args.limit]

    per_variant = len(cases) * args.runs
    estimate = sum(
        per_variant
        * compute_cost_usd(
            VARIANTS[n].model,
            VARIANTS[n].estimated_input_tokens,
            VARIANTS[n].estimated_output_tokens,
        )
        for n in names
    )
    print(
        f"Estimation : {per_variant * len(names)} appels ({len(cases)} factures x {args.runs} "
        f"répétitions x {len(names)} variante(s)), environ {estimate:.2f} $".replace(".", ",")
    )
    if not args.yes:
        print("Rien n'a été dépensé. Relancer avec --yes pour exécuter.")
        return 1

    provider = (provider_factory or _default_provider)()
    engine = create_engine(
        "sqlite://"
    )  # base en mémoire : l'évaluation ne touche pas la vraie base
    init_database(engine)
    results: list[VariantResult] = []
    with Session(engine) as session:
        llm = LLMService(provider, session)
        for name in names:
            print(f"Variante {name} : {VARIANTS[name].description}…")
            results.append(run_variant(name, VARIANTS[name].build(llm), cases, session, args.runs))

    today = date.today()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.report_dir / f"{today.isoformat()}-{args.name}.md"
    report_path.write_text(render_markdown(results, args.runs, today), encoding="utf-8")
    raw_path = args.raw_dir / f"{args.name}.json"
    raw_path.write_text(
        json.dumps(_raw_results(results), ensure_ascii=False, indent=1), encoding="utf-8"
    )

    spent = sum(t.cost_usd for r in results for t in r.trials)
    spent_text = f"{spent:.4f} $".replace(".", ",")
    print(f"Terminé. Coût réel : {spent_text}. Rapport : {report_path}")
    return 0
