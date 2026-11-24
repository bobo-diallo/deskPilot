"""Rend un rapport d'évaluation en Markdown (en français) à partir des résultats des variantes."""

import math
import statistics
from datetime import date

from app.domains.extraction.prompts import EXTRACTION_PROMPTS
from app.evaluation.metrics import FIELDS, paired_bootstrap, summarize, wilson_interval
from app.evaluation.runner import TrialResult, VariantResult

FIELD_LABELS = {
    "supplier_name": "Fournisseur",
    "invoice_number": "Numéro de facture",
    "issue_date": "Date",
    "currency": "Devise",
    "subtotal": "Total hors taxes",
    "tax_amount": "Taxes",
    "total": "Total toutes taxes",
    "line_count": "Nombre de lignes",
    "line_amounts": "Montants des lignes",
    "line_descriptions": "Descriptions des lignes",
}

TAG_LABELS = {
    "digital": "PDF numérique",
    "scan": "Image (scan)",
    "noisy": "Bruité (scan ou enregistrement)",
    "english": "En anglais",
    "multi_tax": "Plusieurs taxes",
    "negative_line": "Ligne de remise",
    "ambiguous_date": "Date ambiguë",
    "thousands": "Montant de 1 000 ou plus",
    "missing_number": "Numéro absent",
    "decimal_quantity": "Quantité décimale",
    "fast": "Débit rapide",
    "canadian_voice": "Voix à accent canadien",
    "spelled_number": "Numéro épelé",
}


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f} %".replace(".", ",")


def _signed_points(value: float) -> str:
    return f"{value * 100:+.1f} pts".replace(".", ",")


def _usd(value: float) -> str:
    return f"{value:.4f} $".replace(".", ",")


def _seconds(ms: float) -> str:
    return f"{ms / 1000:.1f} s".replace(".", ",")


def _p90(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _mean_wer(trials: list[TrialResult]) -> str:
    values = [t.word_error_rate for t in trials if t.word_error_rate is not None]
    return _pct(statistics.mean(values)) if values else "—"


def _compute_ratio(trials: list[TrialResult]) -> str:
    """Médiane de (temps de calcul / durée de l'audio) : moins de 1 = plus vite que la parole."""
    ratios = [t.latency_ms / 1000 / t.audio_seconds for t in trials if t.audio_seconds]
    return f"{statistics.median(ratios):.2f}".replace(".", ",") if ratios else "—"


def _per_case(trials: list[TrialResult], metric) -> dict[str, float]:
    """Moyenne d'une métrique par cas (sur les répétitions), dans l'ordre d'apparition."""
    values: dict[str, list[float]] = {}
    for trial in trials:
        values.setdefault(trial.case_id, []).append(metric(trial))
    return {case_id: sum(v) / len(v) for case_id, v in values.items()}


def render_markdown(variants: list[VariantResult], runs: int, generated_on: date) -> str:
    summaries = {v.name: summarize([t.as_scored() for t in v.trials]) for v in variants}
    case_count = len({t.case_id for t in variants[0].trials})
    names = [v.name for v in variants]

    parts = [
        f"# Rapport d'évaluation — {generated_on.isoformat()}",
        f"Jeu de {case_count} factures, {runs} répétition(s) par facture et par variante.",
    ]

    has_audio = any(t.word_error_rate is not None for v in variants for t in v.trials)
    rows = []
    for v in variants:
        s = summaries[v.name]
        perfect = round(s.perfect_rate * s.trials)
        low, high = wilson_interval(perfect, s.trials)
        latencies = [t.latency_ms for t in v.trials]
        rows.append(
            [
                v.name,
                f"{_pct(s.perfect_rate)} (IC 95 % : {_pct(low)} à {_pct(high)})",
                _usd(statistics.mean(t.cost_usd for t in v.trials)),
                f"{_seconds(statistics.median(latencies))} ({_seconds(_p90(latencies))})",
                str(s.hallucinations),
                str(s.failed),
            ]
        )
        if has_audio:
            row = rows[-1]
            rows[-1] = [
                *row[:2],
                _pct(s.financial_perfect_rate),
                *row[2:4],
                _mean_wer(v.trials),
                _compute_ratio(v.trials),
                *row[4:],
            ]
    header = ["Variante", "Factures parfaites", "Coût par facture", "Latence médiane (p90)",
              "Valeurs inventées", "Échecs"]  # fmt: skip
    if has_audio:
        header[2:2] = ["Montants et date exacts"]
        header[5:5] = ["Erreurs sur les mots", "Temps de calcul / durée audio"]
    parts += ["## Résumé", _table(header, rows)]

    # Quelle consigne a produit ces chiffres : version et empreinte du texte (voir test_prompt_lock)
    versioned = [v for v in variants if v.prompt_version]
    if versioned:
        parts += [
            "## Versions de prompt",
            _table(
                ["Variante", "Version", "Empreinte"],
                [
                    [v.name, v.prompt_version, EXTRACTION_PROMPTS.fingerprint(v.prompt_version)]
                    for v in versioned
                ],
            ),
        ]

    parts += [
        "## Exactitude par champ",
        _table(
            ["Champ", *names],
            [
                [FIELD_LABELS[f], *[_pct(summaries[n].field_accuracy[f]) for n in names]]
                for f in FIELDS
            ],
        ),
    ]

    tags = sorted({tag for s in summaries.values() for tag in s.perfect_rate_by_tag})
    parts += [
        "## Factures parfaites par difficulté",
        _table(
            ["Difficulté", *names],
            [
                [
                    TAG_LABELS.get(tag, tag),
                    *[_pct(summaries[n].perfect_rate_by_tag.get(tag)) for n in names],
                ]
                for tag in tags
            ],
        ),
    ]

    parts += [
        "## Fiabilité du statut « validé »",
        "Une extraction est « validée » quand les montants se recoupent. Mais une erreur "
        "cohérente passe entre les mailles.",
        _table(
            ["Variante", "Part réellement parfaite parmi les « validées »",
             "Erreurs détectées (à relire)", "Erreurs silencieuses"],
            [
                [
                    n,
                    _pct(summaries[n].validated_precision),
                    _pct(summaries[n].error_detection_rate),
                    f"{summaries[n].status_counts['false_accept']} essai(s)",
                ]
                for n in names
            ],
        ),
        "_Erreurs silencieuses_ : extraction fausse, mais marquée « validée ».",
    ]  # fmt: skip

    if len(variants) > 1:
        base = variants[0]
        base_perfect = _per_case(base.trials, lambda t: float(t.score.perfect))
        base_fields = _per_case(
            base.trials, lambda t: sum(t.score.fields.values()) / len(t.score.fields)
        )
        comparison_rows = []
        for other in variants[1:]:
            perfect = _per_case(other.trials, lambda t: float(t.score.perfect))
            fields = _per_case(
                other.trials, lambda t: sum(t.score.fields.values()) / len(t.score.fields)
            )
            shared = [c for c in base_perfect if c in perfect]
            p = paired_bootstrap([perfect[c] for c in shared], [base_perfect[c] for c in shared])
            f = paired_bootstrap([fields[c] for c in shared], [base_fields[c] for c in shared])
            comparison_rows.append(
                [
                    other.name,
                    _signed_points(p.difference),
                    f"{_signed_points(p.low)} à {_signed_points(p.high)}",
                    _signed_points(f.difference),
                    f"{_signed_points(f.low)} à {_signed_points(f.high)}",
                ]
            )
        parts += [
            f"## Comparaison avec la référence ({base.name})",
            "Écart apparié, calculé cas par cas, avec intervalle de confiance à 95 % obtenu en "
            "rééchantillonnant les cas. Si l'intervalle contient 0, l'écart peut être du hasard.",
            _table(
                ["Variante", "Écart de factures parfaites", "IC 95 %",
                 "Écart d'exactitude moyenne par champ", "IC 95 %"],
                comparison_rows,
            ),
        ]  # fmt: skip

    parts += [
        "## Limites",
        "- Factures synthétiques : plus propres que des documents réels ; le bruit des scans "
        "reste léger.",
        f"- Seulement {case_count} cas : les intervalles de confiance sont larges, conclure avec "
        "prudence.",
        "- Les répétitions d'un même cas ne sont pas indépendantes : l'intervalle du résumé est "
        "indicatif, la comparaison appariée est plus fiable.",
        "- Les réponses d'un modèle varient d'un appel à l'autre ; les coûts sont ceux du "
        "journal `api_calls`.",
    ]
    if has_audio:
        parts += [
            "- Dictées en voix de synthèse (macOS) : plus nettes et régulières qu'une voix "
            "humaine ; le bruit ajouté est un bruit blanc léger, loin d'une vraie pièce bruyante.",
            "- « Factures parfaites » exige aussi les noms propres et les descriptions, que "
            "l'oreille (donc Whisper) ne peut pas garantir. La colonne « Montants et date "
            "exacts » a été ajoutée après la première mesure, quand tous les scores sont "
            "tombés à 0 % : c'est une analyse a posteriori, à confirmer sur un jeu neuf.",
            "- Le taux d'erreurs sur les mots compare la transcription au texte lu ; les nombres "
            "sont comparés après retrait de l'espace des milliers.",
        ]
    return "\n\n".join(parts) + "\n"
