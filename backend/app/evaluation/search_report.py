"""Rapport Markdown (en français) de l'évaluation de la recherche dans les documents."""

from datetime import date

from app.evaluation.metrics import paired_bootstrap
from app.evaluation.search_metrics import summarize_ranks
from app.evaluation.search_runner import MODES, QuestionResult

TAG_LABELS = {
    "name_lookup": "Nom du fournisseur dans la question",
    "numeric": "Chiffre précis",
    "paraphrase": "Paraphrase (aucun mot en commun)",
    "cross_doc": "Plusieurs contrats possibles",
}
# Règle d'adoption posée AVANT la mesure (voir docs/architecture.md, ADR 014).
TOLERANCE_MRR = 0.02


def _pct(value: float) -> str:
    return f"{value * 100:.1f} %".replace(".", ",")


def _mrr(value: float) -> str:
    return f"{value:.3f}".replace(".", ",")


def _points(value: float) -> str:
    return f"{value * 100:+.1f} pts".replace(".", ",")


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _reciprocal_ranks(results: list[QuestionResult]) -> list[float]:
    return [1 / r.rank if r.rank else 0.0 for r in results]


def render_search_report(
    results: dict[str, list[QuestionResult]], generated_on: date, embedder_name: str
) -> str:
    summaries = {mode: summarize_ranks([r.rank for r in results[mode]]) for mode in MODES}
    questions = summaries[MODES[0]].questions

    parts = [
        f"# Rapport d'évaluation de la recherche — {generated_on.isoformat()}",
        f"{questions} questions sur 10 contrats fictifs. Modèle d'embeddings : `{embedder_name}`. "
        "Une réponse est juste si le bon morceau du bon contrat est dans les 10 premiers.",
        "## Résumé",
        _table(
            ["Mode", "Rappel@1", "Rappel@3", "Rappel@5", "MRR"],
            [
                [
                    mode,
                    _pct(summaries[mode].recall[1]),
                    _pct(summaries[mode].recall[3]),
                    _pct(summaries[mode].recall[5]),
                    _mrr(summaries[mode].mrr),
                ]
                for mode in MODES
            ],
        ),
    ]

    tags = [tag for tag in TAG_LABELS if any(tag in r.tags for r in results[MODES[0]])]
    rows = []
    for tag in tags:
        row = [TAG_LABELS[tag]]
        for mode in MODES:
            subset = [r.rank for r in results[mode] if tag in r.tags]
            row.append(_mrr(summarize_ranks(subset).mrr))
        rows.append(row)
    parts += ["## MRR par type de question", _table(["Type", *MODES], rows)]

    hybrid = _reciprocal_ranks(results["hybrid"])
    comparison = []
    for other in ("keyword", "vector"):
        diff = paired_bootstrap(hybrid, _reciprocal_ranks(results[other]))
        comparison.append(
            [
                f"hybrid contre {other}",
                _points(diff.difference),
                f"{_points(diff.low)} à {_points(diff.high)}",
            ]
        )
    parts += [
        "## Comparaison appariée (écart de rang réciproque, question par question)",
        "Si l'intervalle contient 0, l'écart peut être du hasard.",
        _table(["Comparaison", "Écart", "IC 95 %"], comparison),
    ]

    best_other = max(summaries["keyword"].mrr, summaries["vector"].mrr)
    satisfied = summaries["hybrid"].mrr >= best_other - TOLERANCE_MRR
    parts += [
        "## Règle de décision (posée avant la mesure)",
        f"Le mode hybride est retenu par défaut si son MRR n'est pas inférieur de plus de "
        f"{_mrr(TOLERANCE_MRR)} au meilleur des deux autres modes. Ici : hybride "
        f"{_mrr(summaries['hybrid'].mrr)}, meilleur des deux autres {_mrr(best_other)} : "
        f"règle {'satisfaite' if satisfied else 'non satisfaite'}.",
        "## Limites",
        "- Documents et questions écrits par la même personne : les questions ressemblent "
        "peut-être plus aux textes que celles d'un vrai utilisateur.",
        f"- Seulement {questions} questions et 10 contrats : les écarts doivent être lus avec "
        "leur intervalle de confiance.",
        "- Paramètres d'usage, non réglés sur ces données (BM25 : k1 = 1,5 et b = 0,75 ; "
        "fusion : k = 60).",
        "- Un seul modèle d'embeddings essayé ; un autre pourrait changer le classement.",
    ]
    return "\n\n".join(parts) + "\n"
