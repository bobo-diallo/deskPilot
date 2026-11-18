from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.domains.documents.models import Document
from app.domains.extraction.models import Extraction, ExtractionStatus
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.review.errors import (
    ExtractionNotFoundError,
    InvalidCorrectionError,
    NotReviewableError,
)
from app.domains.review.models import ReviewDecision
from app.domains.review.service import ReviewService


def make_invoice(**changes) -> Invoice:
    values = dict(
        supplier_name="Plomberie Tremblée",  # erreur de transcription typique
        invoice_number="2026-014",
        issue_date=date(2026, 3, 3),
        currency="EUR",
        lines=[
            InvoiceLine(
                description="Réparation",
                quantity=Decimal("1"),
                unit_price=Decimal("1000.00"),
                total=Decimal("1000.00"),
            )
        ],
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("200.00"),
        total=Decimal("1200.00"),
    )
    values.update(changes)
    return Invoice(**values)


def add_extraction(session, status=ExtractionStatus.NEEDS_REVIEW, issues=None, **changes):
    document = Document(filename="d.wav", media_type="audio/wav")
    session.add(document)
    session.commit()
    extraction = Extraction(
        document_id=document.id,
        document_type="invoice",
        status=status.value,
        data=make_invoice(**changes).model_dump(mode="json"),
        issues=issues or [{"code": "from_audio", "field": None, "message": "dictée"}],
        model="claude-haiku-5-5",
    )
    session.add(extraction)
    session.commit()
    return extraction


def test_the_queue_lists_only_extractions_to_review_oldest_first(session):
    first = add_extraction(session)
    add_extraction(session, status=ExtractionStatus.VALIDATED, issues=[])
    third = add_extraction(session)

    assert [e.id for e in ReviewService(session).pending()] == [first.id, third.id]


def test_approving_keeps_the_data_and_records_the_decision(session):
    extraction = add_extraction(session)

    result = ReviewService(session).approve(extraction.id, comment="Vérifié sur la pièce")

    assert result.status == ExtractionStatus.APPROVED
    decision = session.scalars(select(ReviewDecision)).one()
    assert decision.decision == "approved"
    assert decision.comment == "Vérifié sur la pièce"
    assert decision.changed_fields == []
    assert decision.after is None


def test_correcting_replaces_the_data_and_keeps_the_original_in_the_audit_trail(session):
    extraction = add_extraction(session)
    original = dict(extraction.data)

    result = ReviewService(session).correct(
        extraction.id, make_invoice(supplier_name="Plomberie Tremblay")
    )

    assert result.status == ExtractionStatus.CORRECTED
    assert result.data["supplier_name"] == "Plomberie Tremblay"
    decision = session.scalars(select(ReviewDecision)).one()
    assert decision.before == original  # on peut toujours savoir ce que le système avait lu
    assert decision.after["supplier_name"] == "Plomberie Tremblay"
    assert decision.changed_fields == ["supplier_name"]


def test_a_correction_is_revalidated_and_drops_the_audio_reason(session):
    extraction = add_extraction(session)

    result = ReviewService(session).correct(extraction.id, make_invoice(supplier_name="Tremblay"))

    assert result.issues == []  # un humain a relu : le motif « dictée » n'a plus lieu d'être


def test_a_correction_that_is_still_inconsistent_keeps_its_issues_visible(session):
    extraction = add_extraction(session)

    result = ReviewService(session).correct(extraction.id, make_invoice(total=Decimal("999.00")))

    assert result.status == ExtractionStatus.CORRECTED
    assert [issue["code"] for issue in result.issues] == ["total_mismatch"]


def test_a_correction_that_changes_nothing_is_refused(session):
    extraction = add_extraction(session)

    with pytest.raises(InvalidCorrectionError, match="approuver"):
        ReviewService(session).correct(extraction.id, make_invoice())

    assert session.scalars(select(ReviewDecision)).all() == []


def test_rejecting_records_the_reason(session):
    extraction = add_extraction(session)

    result = ReviewService(session).reject(extraction.id, comment="Illisible")

    assert result.status == ExtractionStatus.REJECTED
    assert session.scalars(select(ReviewDecision)).one().comment == "Illisible"


def test_an_extraction_can_only_be_reviewed_once(session):
    extraction = add_extraction(session)
    service = ReviewService(session)
    service.approve(extraction.id)

    with pytest.raises(NotReviewableError):
        service.reject(extraction.id)

    assert len(session.scalars(select(ReviewDecision)).all()) == 1


def test_an_automatically_validated_extraction_is_not_in_the_review_flow(session):
    extraction = add_extraction(session, status=ExtractionStatus.VALIDATED, issues=[])

    with pytest.raises(NotReviewableError):
        ReviewService(session).approve(extraction.id)


def test_an_unknown_extraction_is_reported(session):
    with pytest.raises(ExtractionNotFoundError):
        ReviewService(session).approve(999)


def test_statistics_count_decisions_and_corrected_fields(session):
    service = ReviewService(session)
    service.approve(add_extraction(session).id)
    service.correct(add_extraction(session).id, make_invoice(supplier_name="A"))
    service.correct(
        add_extraction(session).id,
        make_invoice(supplier_name="B", invoice_number="2026-015"),
    )
    service.reject(add_extraction(session).id)

    stats = service.stats()

    assert (stats.reviewed, stats.approved, stats.corrected, stats.rejected) == (4, 1, 2, 1)
    assert stats.correction_rate == 0.5
    assert stats.field_corrections == {"supplier_name": 2, "invoice_number": 1}


def test_statistics_of_an_empty_history_have_no_rate(session):
    stats = ReviewService(session).stats()

    assert stats.reviewed == 0
    assert stats.correction_rate is None
    assert stats.field_corrections == {}


def test_a_failure_while_correcting_leaves_no_half_recorded_decision(session, monkeypatch):
    extraction = add_extraction(session)
    original_data = dict(extraction.data)

    def broken_validation(invoice):
        raise RuntimeError("panne pendant la revalidation")

    monkeypatch.setattr("app.domains.review.service.validate_invoice", broken_validation)

    with pytest.raises(RuntimeError):
        ReviewService(session).correct(extraction.id, make_invoice(supplier_name="Tremblay"))
    session.rollback()  # ce que ferait la session de requête à la fermeture

    assert session.scalars(select(ReviewDecision)).all() == []
    refreshed = session.get(Extraction, extraction.id)
    assert refreshed.status == ExtractionStatus.NEEDS_REVIEW
    assert refreshed.data == original_data
