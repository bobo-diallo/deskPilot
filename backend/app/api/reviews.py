from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.api.extractions import ExtractionResult, find_transcription, to_result
from app.domains.extraction.models import Extraction
from app.domains.extraction.schemas import Invoice
from app.domains.review.errors import (
    ExtractionNotFoundError,
    InvalidCorrectionError,
    NotReviewableError,
)
from app.domains.review.service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


class DecisionRequest(BaseModel):
    comment: str | None = None


class CorrectionRequest(BaseModel):
    data: Invoice  # la facture telle qu'elle doit être ; validée par Pydantic à la réception
    comment: str | None = None


class ReviewStatsResult(BaseModel):
    reviewed: int
    approved: int
    corrected: int
    rejected: int
    correction_rate: float | None
    field_corrections: dict[str, int]


def _result(session: Session, extraction: Extraction) -> ExtractionResult:
    return to_result(extraction, find_transcription(session, extraction.id))


def _as_http_error(error: Exception) -> HTTPException:
    """Traduit une erreur du domaine en réponse HTTP : le domaine ignore HTTP."""
    if isinstance(error, ExtractionNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, NotReviewableError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


@router.get("")
def list_pending_reviews(
    session: Annotated[Session, Depends(get_db_session)],
) -> list[ExtractionResult]:
    return [_result(session, extraction) for extraction in ReviewService(session).pending()]


@router.get("/stats")
def review_stats(session: Annotated[Session, Depends(get_db_session)]) -> ReviewStatsResult:
    stats = ReviewService(session).stats()
    return ReviewStatsResult(**stats.__dict__)


@router.post("/{extraction_id}/approve")
def approve(
    extraction_id: int,
    body: DecisionRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ExtractionResult:
    try:
        extraction = ReviewService(session).approve(extraction_id, body.comment)
    except (ExtractionNotFoundError, NotReviewableError) as error:
        raise _as_http_error(error) from error
    return _result(session, extraction)


@router.post("/{extraction_id}/reject")
def reject(
    extraction_id: int,
    body: DecisionRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ExtractionResult:
    try:
        extraction = ReviewService(session).reject(extraction_id, body.comment)
    except (ExtractionNotFoundError, NotReviewableError) as error:
        raise _as_http_error(error) from error
    return _result(session, extraction)


@router.post("/{extraction_id}/correct")
def correct(
    extraction_id: int,
    body: CorrectionRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ExtractionResult:
    try:
        extraction = ReviewService(session).correct(extraction_id, body.data, body.comment)
    except (ExtractionNotFoundError, NotReviewableError, InvalidCorrectionError) as error:
        raise _as_http_error(error) from error
    return _result(session, extraction)
