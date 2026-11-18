from datetime import date
from decimal import Decimal

import pytest

from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.extractors.audio import AudioExtractor
from app.domains.extraction.schemas import Invoice
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService
from app.domains.transcription.errors import TranscriptionError
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


def build(session, transcriber=None, model=None):
    provider = FakeProvider(parsed=make_invoice())
    transcriber = transcriber or FakeTranscriber(text="Facture Plomberie Tremblay numéro 2026-014")
    extractor = AudioExtractor(transcriber, LLMService(provider, session), model=model)
    return provider, transcriber, extractor


def test_only_the_transcribed_text_is_sent_to_the_model(session):
    provider, _, extractor = build(session)

    extractor.extract(b"audio", "audio/wav")

    request = provider.received[0]
    assert request.attachments == []  # l'audio ne quitte jamais la machine
    assert "Facture Plomberie Tremblay numéro 2026-014" in request.messages[0].content
    assert request.response_schema is Invoice


def test_the_model_is_warned_that_the_text_is_a_dictation(session):
    provider, _, extractor = build(session)

    extractor.extract(b"audio", "audio/wav")

    instruction = provider.received[0].messages[0].content
    assert "dictée" in instruction
    assert "nombres" in instruction  # consigne sur les nombres écrits en lettres


def test_the_output_carries_the_data_the_model_and_the_transcript(session):
    _, _, extractor = build(session, model="claude-haiku-5-5")

    output = extractor.extract(b"audio", "audio/wav")

    assert output.data == make_invoice()
    assert output.model == "claude-haiku-5-5"
    assert output.transcript is not None
    assert output.transcript.text == "Facture Plomberie Tremblay numéro 2026-014"


def test_the_audio_is_given_to_the_transcriber(session):
    _, transcriber, extractor = build(session)

    extractor.extract(b"mon-audio", "audio/mpeg")

    assert transcriber.received == [b"mon-audio"]


def test_a_non_audio_file_is_refused_without_transcribing(session):
    provider, transcriber, extractor = build(session)

    with pytest.raises(ExtractionError, match="audio"):
        extractor.extract(b"%PDF-", "application/pdf")

    assert transcriber.received == []
    assert provider.received == []


def test_an_empty_transcript_is_refused_without_calling_the_model(session):
    provider, _, extractor = build(session, transcriber=FakeTranscriber(text="  "))

    with pytest.raises(ExtractionError, match="Aucune parole"):
        extractor.extract(b"silence", "audio/wav")

    assert provider.received == []


def test_a_transcription_failure_becomes_an_extraction_error(session):
    class BrokenTranscriber:
        def transcribe(self, content, language=None):
            raise TranscriptionError("fichier illisible")

    provider, _, extractor = build(session, transcriber=BrokenTranscriber())

    with pytest.raises(ExtractionError, match="fichier illisible"):
        extractor.extract(b"corrompu", "audio/wav")

    assert provider.received == []
