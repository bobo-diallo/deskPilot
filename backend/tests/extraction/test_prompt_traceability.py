import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import get_llm_provider
from app.domains.documents.models import Document
from app.domains.extraction.extractors.audio import AudioExtractor
from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.extractors.text_layer import TextLayerExtractor
from app.domains.extraction.models import Extraction
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.prompts import DEFAULT_PROMPT_VERSION
from app.domains.extraction.schemas import Invoice
from app.domains.extraction.service import ExtractionService
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService
from app.domains.transcription.transcribers.fake import FakeTranscriber
from app.evaluation.variants import VARIANTS
from app.main import create_app
from tests.extraction.test_service import make_invoice


def text_pdf() -> bytes:
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, "Facture")
    pdf.save()
    return buffer.getvalue()


def llm(session) -> LLMService:
    return LLMService(FakeProvider(parsed=Invoice()), session)


def test_the_vision_extractor_reports_the_version_it_used(session):
    output = ClaudeExtractor(llm(session), prompt_version="v1").extract(
        b"%PDF-1", "application/pdf"
    )

    assert output.prompt_version == "v1"


def test_the_default_version_is_reported_when_none_is_requested(session):
    output = ClaudeExtractor(llm(session)).extract(b"%PDF-1", "application/pdf")

    assert output.prompt_version == DEFAULT_PROMPT_VERSION


def test_the_text_extractor_reports_the_version_it_used(session):
    output = TextLayerExtractor(llm(session), prompt_version="v1").extract(
        text_pdf(), "application/pdf"
    )

    assert output.prompt_version == "v1"


def test_the_audio_extractor_reports_the_version_it_used(session):
    extractor = AudioExtractor(FakeTranscriber(text="Facture"), llm(session), prompt_version="v1")

    assert extractor.extract(b"RIFF....WAVE", "audio/wav").prompt_version == "v1"


@pytest.mark.parametrize("name", list(VARIANTS))
def test_an_evaluation_variant_declares_the_version_its_extractor_really_uses(session, name):
    spec = VARIANTS[name]

    extractor = spec.build(llm(session))

    # Attribut interne : les variantes audio ne peuvent pas être exécutées sans modèle Whisper.
    assert extractor._prompt_version == spec.prompt_version


class FixedExtractor:
    def __init__(self, prompt_version):
        self._version = prompt_version

    def extract(self, content, media_type):
        return ExtractionOutput(data=make_invoice("25.00"), model="m", prompt_version=self._version)


def saved_version(session, prompt_version):
    document = Document(filename="f.pdf", media_type="application/pdf")
    session.add(document)
    session.commit()
    ExtractionService(FixedExtractor(prompt_version), session).extract_invoice(document, b"x")
    return session.scalars(select(Extraction)).one().prompt_version


def test_the_version_is_saved_with_the_extraction(session):
    assert saved_version(session, "v2-date-convention") == "v2-date-convention"


def test_an_extractor_without_a_version_leaves_it_empty(session):
    assert saved_version(session, None) is None


def test_the_api_returns_the_prompt_version(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    application = create_app()
    application.dependency_overrides[get_llm_provider] = lambda: FakeProvider(
        parsed=make_invoice("25.00")
    )

    with TestClient(application) as client:
        created = client.post(
            "/extractions",
            files={"file": ("f.pdf", b"%PDF-1.4 x", "application/octet-stream")},
            data={"document_type": "invoice"},
        ).json()
        read_back = client.get(f"/extractions/{created['id']}").json()

    assert created["prompt_version"] == DEFAULT_PROMPT_VERSION
    assert read_back["prompt_version"] == DEFAULT_PROMPT_VERSION
