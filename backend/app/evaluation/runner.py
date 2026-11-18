import time
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.extraction.models import ExtractionStatus
from app.domains.extraction.ports import DocumentExtractor
from app.domains.extraction.validation import validate_invoice
from app.domains.llm.models import ApiCall
from app.evaluation.dataset import DatasetCase
from app.evaluation.metrics import CaseScore, ScoredTrial, score_extraction, word_error_rate


@dataclass(frozen=True)
class TrialResult:
    """Un essai : un cas extrait une fois, avec son score, son coût et sa latence."""

    case_id: str
    tags: tuple[str, ...]
    run: int
    score: CaseScore
    model: str | None
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    error: str | None
    # Renseignés seulement pour les enregistrements :
    word_error_rate: float | None = None
    audio_seconds: float | None = None

    def as_scored(self) -> ScoredTrial:
        return ScoredTrial(self.case_id, self.tags, self.score)


@dataclass(frozen=True)
class VariantResult:
    name: str
    trials: list[TrialResult]


def run_variant(
    name: str,
    extractor: DocumentExtractor,
    cases: list[DatasetCase],
    session: Session,
    runs: int = 3,
) -> VariantResult:
    """Fait tourner un extracteur sur tout le jeu, `runs` fois chacun.

    Les coûts et les tokens sont relus dans le journal `api_calls` (même source de vérité
    que l'application). Une session dédiée à l'évaluation évite de polluer la vraie base.
    """
    trials: list[TrialResult] = []
    for case in cases:
        content = case.path.read_bytes()
        for run in range(1, runs + 1):
            last_id = session.scalar(select(func.coalesce(func.max(ApiCall.id), 0)))
            started_at = time.perf_counter()
            error = None
            output = None
            try:
                output = extractor.extract(content, case.media_type)
            except (
                Exception
            ) as exc:  # noqa: BLE001 - un essai raté ne doit pas arrêter une mesure payante
                error = f"{type(exc).__name__}: {exc}"
            latency_ms = round((time.perf_counter() - started_at) * 1000)

            calls = session.scalars(select(ApiCall).where(ApiCall.id > last_id)).all()
            if output is None:
                score = score_extraction(case.expected, None, status=None)
            else:
                issues = validate_invoice(output.data)
                status = ExtractionStatus.NEEDS_REVIEW if issues else ExtractionStatus.VALIDATED
                score = score_extraction(case.expected, output.data, status.value)

            transcript = output.transcript if output else None
            wer = None
            if transcript and case.spoken:
                wer = word_error_rate(case.spoken, transcript.text)

            trials.append(
                TrialResult(
                    case_id=case.case_id,
                    tags=case.tags,
                    run=run,
                    score=score,
                    model=output.model if output else None,
                    input_tokens=sum(call.input_tokens for call in calls),
                    output_tokens=sum(call.output_tokens for call in calls),
                    cost_usd=sum(call.cost_usd for call in calls),
                    latency_ms=latency_ms,
                    error=error,
                    word_error_rate=wer,
                    audio_seconds=transcript.duration_seconds if transcript else None,
                )
            )
    return VariantResult(name=name, trials=trials)
