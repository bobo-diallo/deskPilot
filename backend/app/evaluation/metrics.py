"""Métriques d'évaluation : fonctions pures, sans réseau ni base de données.

On compare une facture extraite à la vérité terrain, champ par champ, puis on agrège.
"""

import math
import random
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domains.extraction.schemas import Invoice

SCALAR_FIELDS = (
    "supplier_name",
    "invoice_number",
    "issue_date",
    "currency",
    "subtotal",
    "tax_amount",
    "total",
)
LINE_FIELDS = ("line_count", "line_amounts", "line_descriptions")
FIELDS = SCALAR_FIELDS + LINE_FIELDS

# Deux montants à moins d'un demi-centime d'écart sont considérés égaux.
AMOUNT_TOLERANCE = Decimal("0.005")


@dataclass(frozen=True)
class CaseScore:
    """Résultat de la comparaison d'une extraction avec sa vérité terrain."""

    fields: dict[str, bool]
    hallucinations: int  # champs absents du document pour lesquels une valeur a été inventée
    status: str | None  # statut attribué par la validation ("validated" ou "needs_review")
    failed: bool  # l'extraction n'a pas abouti du tout

    @property
    def perfect(self) -> bool:
        return all(self.fields.values())


@dataclass(frozen=True)
class ScoredTrial:
    """Un essai : un cas du jeu de données extrait une fois."""

    case_id: str
    tags: tuple[str, ...]
    score: CaseScore


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def _same(expected: object, extracted: object) -> bool:
    if expected is None or extracted is None:
        return expected is None and extracted is None
    if isinstance(expected, Decimal):
        return abs(expected - extracted) < AMOUNT_TOLERANCE
    if isinstance(expected, str):
        return _normalize(expected) == _normalize(extracted)
    if isinstance(expected, date):
        return expected == extracted
    return expected == extracted


def score_extraction(expected: Invoice, extracted: Invoice | None, status: str | None) -> CaseScore:
    if extracted is None:
        return CaseScore(
            fields=dict.fromkeys(FIELDS, False), hallucinations=0, status=None, failed=True
        )

    fields: dict[str, bool] = {}
    hallucinations = 0
    for name in SCALAR_FIELDS:
        wanted, got = getattr(expected, name), getattr(extracted, name)
        fields[name] = _same(wanted, got)
        if wanted is None and got is not None:
            hallucinations += 1

    same_count = len(expected.lines) == len(extracted.lines)
    fields["line_count"] = same_count
    if same_count:
        pairs = list(zip(expected.lines, extracted.lines, strict=True))
        fields["line_amounts"] = all(
            _same(e.quantity, g.quantity)
            and _same(e.unit_price, g.unit_price)
            and _same(e.total, g.total)
            for e, g in pairs
        )
        fields["line_descriptions"] = all(_same(e.description, g.description) for e, g in pairs)
    else:
        fields["line_amounts"] = False
        fields["line_descriptions"] = False

    return CaseScore(fields=fields, hallucinations=hallucinations, status=status, failed=False)


def status_outcome(score: CaseScore) -> str:
    """Classe le statut attribué par la validation, au regard de la vérité."""
    if score.failed:
        return "failed"
    if score.status == "validated":
        return (
            "true_accept" if score.perfect else "false_accept"
        )  # false_accept : erreur silencieuse
    return "false_alarm" if score.perfect else "caught"


@dataclass(frozen=True)
class Summary:
    trials: int
    failed: int
    perfect_rate: float
    field_accuracy: dict[str, float]
    hallucinations: int
    perfect_rate_by_tag: dict[str, float]
    status_counts: dict[str, int]
    # Parmi les extractions « validated », part qui est réellement parfaite.
    validated_precision: float | None
    # Parmi les extractions erronées, part signalée « needs_review » (donc rattrapée).
    error_detection_rate: float | None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(trials: list[ScoredTrial]) -> Summary:
    scores = [trial.score for trial in trials]

    tags = sorted({tag for trial in trials for tag in trial.tags})
    by_tag = {tag: _mean([float(t.score.perfect) for t in trials if tag in t.tags]) for tag in tags}

    counts = dict.fromkeys(("true_accept", "false_accept", "false_alarm", "caught"), 0)
    for score in scores:
        outcome = status_outcome(score)
        if outcome in counts:
            counts[outcome] += 1

    accepted = counts["true_accept"] + counts["false_accept"]
    wrong = counts["false_accept"] + counts["caught"]
    return Summary(
        trials=len(trials),
        failed=sum(score.failed for score in scores),
        perfect_rate=_mean([float(score.perfect) for score in scores]),
        field_accuracy={name: _mean([float(s.fields[name]) for s in scores]) for name in FIELDS},
        hallucinations=sum(score.hallucinations for score in scores),
        perfect_rate_by_tag=by_tag,
        status_counts=counts,
        validated_precision=counts["true_accept"] / accepted if accepted else None,
        error_detection_rate=counts["caught"] / wrong if wrong else None,
    )


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalle de confiance à 95 % d'une proportion (méthode de Wilson).

    Avec peu d'essais, une proportion seule trompe : 8 sur 10 peut aussi bien être 49 % que 94 %.
    """
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denominator
    return (center - half, center + half)


@dataclass(frozen=True)
class BootstrapResult:
    difference: float  # moyenne de A moins moyenne de B
    low: float  # borne basse de l'intervalle à 95 %
    high: float


def paired_bootstrap(
    a: list[float], b: list[float], seed: int = 0, resamples: int = 2000
) -> BootstrapResult:
    """Écart entre deux variantes, avec intervalle de confiance, en rééchantillonnant les cas.

    `a[i]` et `b[i]` sont les scores des deux variantes sur le même cas i (comparaison appariée).
    Si l'intervalle contient 0, l'écart observé peut n'être que du hasard.
    """
    if len(a) != len(b) or not a:
        raise ValueError("Les deux listes doivent avoir la même longueur, non nulle")
    rng = random.Random(seed)
    size = len(a)
    differences = []
    for _ in range(resamples):
        picks = [rng.randrange(size) for _ in range(size)]
        differences.append(sum(a[i] - b[i] for i in picks) / size)
    differences.sort()
    return BootstrapResult(
        difference=_mean(a) - _mean(b),
        low=differences[int(0.025 * (resamples - 1))],
        high=differences[int(0.975 * (resamples - 1))],
    )
