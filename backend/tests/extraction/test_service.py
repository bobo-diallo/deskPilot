from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.domains.documents.models import Document
from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.models import Extraction, ExtractionStatus
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.extraction.service import ExtractionService
from app.domains.llm.models import ApiCall
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService


def make_invoice(total: str = "30.00") -> Invoice:
    return Invoice(
        supplier_name="Atelier Nord",
        invoice_number="2026-014",
        issue_date=date(2026, 11, 12),
        currency="EUR",
        lines=[
            InvoiceLine(
                description="Chaise",
                quantity=Decimal("2"),
                unit_price=Decimal("10.00"),
                total=Decimal("20.00"),
            ),
            InvoiceLine(
                description="Livraison",
                quantity=Decimal("1"),
                unit_price=Decimal("5.00"),
                total=Decimal("5.00"),
            ),
        ],
        subtotal=Decimal("25.00"),
        tax_amount=Decimal("5.00"),
        total=Decimal(total),
    )


def build(session, parsed):
    provider = FakeProvider(parsed=parsed, input_tokens=1_000, output_tokens=500)
    extractor = ClaudeExtractor(LLMService(provider, session))
    return provider, ExtractionService(extractor, session)


@pytest.fixture
def document(session) -> Document:
    document = Document(filename="facture.pdf", media_type="application/pdf")
    session.add(document)
    session.commit()
    return document


def test_extractor_sends_the_file_and_asks_for_the_invoice_schema(session):
    provider, _ = build(session, make_invoice())

    ClaudeExtractor(LLMService(provider, session)).extract(b"%PDF-1", "application/pdf")

    request = provider.received[0]
    assert request.response_schema is Invoice
    assert request.attachments[0].media_type == "application/pdf"
    assert request.attachments[0].data == b"%PDF-1"
    assert request.model == "claude-sonnet-5-5"  # tâche d'extraction -> modèle le plus capable


def test_extractor_fails_clearly_when_the_model_returns_no_structured_data(session):
    provider = FakeProvider(parsed=None)
    extractor = ClaudeExtractor(LLMService(provider, session))

    with pytest.raises(ExtractionError):
        extractor.extract(b"%PDF-1", "application/pdf")


def test_a_consistent_invoice_is_validated_and_stored(session, document):
    _, service = build(session, make_invoice())

    extraction = service.extract_invoice(document, b"%PDF-1")

    assert extraction.status == ExtractionStatus.VALIDATED
    assert extraction.document_id == document.id
    assert extraction.data["supplier_name"] == "Atelier Nord"
    assert extraction.issues == []
    assert extraction.model == "claude-sonnet-5-5"
    assert session.scalars(select(Extraction)).one().id == extraction.id


def test_an_inconsistent_invoice_needs_review_and_lists_its_issues(session, document):
    _, service = build(session, make_invoice(total="99.00"))

    extraction = service.extract_invoice(document, b"%PDF-1")

    assert extraction.status == ExtractionStatus.NEEDS_REVIEW
    assert [issue["code"] for issue in extraction.issues] == ["total_mismatch"]
    assert extraction.issues[0]["message"]


def test_the_extraction_cost_is_recorded_in_the_journal(session, document):
    _, service = build(session, make_invoice())

    service.extract_invoice(document, b"%PDF-1")

    call = session.scalars(select(ApiCall)).one()
    assert call.model == "claude-sonnet-5-5"
    assert call.cost_usd == pytest.approx(0.007)  # (1000 x 2 + 500 x 10) / 1 000 000
