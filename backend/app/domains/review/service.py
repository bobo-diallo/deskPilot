from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.extraction.models import Extraction, ExtractionStatus
from app.domains.extraction.schemas import Invoice
from app.domains.extraction.validation import validate_invoice
from app.domains.review.errors import (
    ExtractionNotFoundError,
    InvalidCorrectionError,
    NotReviewableError,
)
from app.domains.review.models import ReviewDecision


@dataclass(frozen=True)
class ReviewStats:
    reviewed: int
    approved: int
    corrected: int
    rejected: int
    correction_rate: float | None  # part des relectures qui ont abouti à une correction
    field_corrections: dict[str, int]  # combien de fois chaque champ a été corrigé


class ReviewService:
    """File de revue humaine : lister ce qui attend, puis approuver, corriger ou rejeter."""

    def __init__(self, session: Session):
        self._session = session

    def pending(self) -> list[Extraction]:
        """Extractions à relire, les plus anciennes d'abord (premier arrivé, premier servi)."""
        query = (
            select(Extraction)
            .where(Extraction.status == ExtractionStatus.NEEDS_REVIEW.value)
            .order_by(Extraction.created_at, Extraction.id)
        )
        return list(self._session.scalars(query))

    def approve(self, extraction_id: int, comment: str | None = None) -> Extraction:
        extraction = self._reviewable(extraction_id)
        self._record(extraction, ExtractionStatus.APPROVED, after=None, changed=[], comment=comment)
        self._session.commit()
        return extraction

    def reject(self, extraction_id: int, comment: str | None = None) -> Extraction:
        extraction = self._reviewable(extraction_id)
        self._record(extraction, ExtractionStatus.REJECTED, after=None, changed=[], comment=comment)
        self._session.commit()
        return extraction

    def correct(
        self, extraction_id: int, corrected: Invoice, comment: str | None = None
    ) -> Extraction:
        extraction = self._reviewable(extraction_id)
        original = Invoice.model_validate(extraction.data)
        changed = [
            name
            for name in Invoice.model_fields
            if getattr(original, name) != getattr(corrected, name)
        ]
        if not changed:
            raise InvalidCorrectionError(
                "Aucune modification : utiliser « approuver » si l'extraction est juste"
            )
        self._record(
            extraction,
            ExtractionStatus.CORRECTED,
            after=corrected.model_dump(mode="json"),
            changed=changed,
            comment=comment,
        )
        # La correction repasse par les contrôles ; le motif « dictée » disparaît, car un
        # humain a relu. Une incohérence restante reste visible.
        extraction.data = corrected.model_dump(mode="json")
        extraction.issues = [
            {"code": issue.code.value, "field": issue.field, "message": issue.message}
            for issue in validate_invoice(corrected)
        ]
        self._session.commit()
        return extraction

    def stats(self) -> ReviewStats:
        decisions = list(self._session.scalars(select(ReviewDecision)))
        counts = Counter(decision.decision for decision in decisions)
        fields = Counter(name for decision in decisions for name in decision.changed_fields)
        reviewed = len(decisions)
        return ReviewStats(
            reviewed=reviewed,
            approved=counts["approved"],
            corrected=counts["corrected"],
            rejected=counts["rejected"],
            correction_rate=counts["corrected"] / reviewed if reviewed else None,
            field_corrections=dict(fields),
        )

    def _reviewable(self, extraction_id: int) -> Extraction:
        extraction = self._session.get(Extraction, extraction_id)
        if extraction is None:
            raise ExtractionNotFoundError(f"Extraction {extraction_id} introuvable")
        if extraction.status != ExtractionStatus.NEEDS_REVIEW.value:
            raise NotReviewableError(
                f"L'extraction {extraction_id} n'est pas à relire (statut : {extraction.status})"
            )
        return extraction

    def _record(
        self,
        extraction: Extraction,
        status: ExtractionStatus,
        after: dict | None,
        changed: list[str],
        comment: str | None,
    ) -> None:
        self._session.add(
            ReviewDecision(
                extraction_id=extraction.id,
                decision=status.value,
                before=dict(extraction.data),
                after=after,
                changed_fields=changed,
                comment=comment,
            )
        )
        extraction.status = status.value
        # Pas de commit ici : chaque opération publique valide tout d'un seul coup (atomicité).
