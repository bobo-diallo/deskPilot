from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.domains.documents.models import Document
from app.domains.extraction.extractors.audio import AudioExtractor
from app.domains.extraction.extractors.dispatch import MediaTypeExtractor
from app.domains.extraction.models import Extraction
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.extraction.service import ExtractionService
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService
from app.domains.transcription.models import Transcription
from app.domains.transcription.transcribers.fake import FakeTranscriber


def make_invoice() -> Invoice:
    return Invoice(
        supplier_name="Plomberie Tremblay",
        invoice_number="2026-014",
        issue_date=date(2026, 3, 3),
        currency="EUR",
        lines=[],
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("234.50"),
        total=Decimal("1234.50"),
    )


class StaticExtractor:
    """Extracteur qui renvoie un résultat fixe et note le type reçu."""

    def __init__(self, label: str):
        self.label = label
        self.calls: list[str] = []

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput:
        self.calls.append(media_type)
        return ExtractionOutput(data=make_invoice(), model=self.label)


@pytest.fixture
def audio_document(session) -> Document:
    document = Document(filename="dictee.wav", media_type="audio/wav")
    session.add(document)
    session.commit()
    return document


def test_the_transcript_is_saved_with_the_extraction(session, audio_document):
    transcriber = FakeTranscriber(text="Facture Tremblay", duration_seconds=5.5)
    extractor = AudioExtractor(
        transcriber, LLMService(FakeProvider(parsed=make_invoice()), session)
    )

    extraction = ExtractionService(extractor, session).extract_invoice(audio_document, b"son")

    saved = session.scalars(select(Transcription)).one()
    assert saved.extraction_id == extraction.id
    assert saved.text == "Facture Tremblay"
    assert saved.duration_seconds == 5.5
    assert saved.model == "fake"


def test_no_transcript_is_saved_for_a_pdf(session):
    document = Document(filename="f.pdf", media_type="application/pdf")
    session.add(document)
    session.commit()

    ExtractionService(StaticExtractor("pdf"), session).extract_invoice(document, b"%PDF-")

    assert session.scalars(select(Transcription)).all() == []
    assert session.scalars(select(Extraction)).one() is not None


def test_the_dispatcher_sends_audio_to_the_audio_extractor_and_the_rest_to_the_other():
    visual, audio = StaticExtractor("visual"), StaticExtractor("audio")
    dispatcher = MediaTypeExtractor(visual=visual, audio=audio)

    assert dispatcher.extract(b"x", "audio/wav").model == "audio"
    assert dispatcher.extract(b"x", "application/pdf").model == "visual"
    assert dispatcher.extract(b"x", "image/png").model == "visual"
    assert audio.calls == ["audio/wav"]
    assert visual.calls == ["application/pdf", "image/png"]


def test_an_extraction_from_audio_always_needs_review_even_when_amounts_add_up(
    session, audio_document
):
    from app.domains.extraction.models import ExtractionStatus

    consistent = make_invoice().model_copy(
        update={
            "lines": [
                InvoiceLine(
                    description="Réparation",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1000.00"),
                    total=Decimal("1000.00"),
                )
            ]
        }
    )
    extractor = AudioExtractor(
        FakeTranscriber(text="Facture Tremblay"),
        LLMService(FakeProvider(parsed=consistent), session),
    )

    extraction = ExtractionService(extractor, session).extract_invoice(audio_document, b"son")

    assert extraction.status == ExtractionStatus.NEEDS_REVIEW
    assert extraction.issues == [
        {
            "code": "from_audio",
            "field": None,
            "message": "Extraction issue d'une dictée : relecture obligatoire",
        }
    ]


def test_the_audio_reason_is_added_to_real_issues_not_substituted(session, audio_document):
    extractor = AudioExtractor(
        FakeTranscriber(text="Facture Tremblay"),
        LLMService(FakeProvider(parsed=make_invoice().model_copy(update={"total": None})), session),
    )

    extraction = ExtractionService(extractor, session).extract_invoice(audio_document, b"son")

    codes = [issue["code"] for issue in extraction.issues]
    assert "from_audio" in codes
    assert "missing_field" in codes
