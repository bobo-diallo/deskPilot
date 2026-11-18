from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_llm_provider, get_transcriber
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.llm.providers.fake import FakeProvider
from app.domains.transcription.transcribers.fake import FakeTranscriber
from app.main import create_app

PDF = b"%PDF-1.4 fausse facture"
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt fausse dictee"


def make_invoice() -> Invoice:
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
            )
        ],
        subtotal=Decimal("20.00"),
        tax_amount=Decimal("4.00"),
        total=Decimal("24.00"),
    )


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    application = create_app()
    application.dependency_overrides[get_llm_provider] = lambda: FakeProvider(parsed=make_invoice())
    application.dependency_overrides[get_transcriber] = lambda: FakeTranscriber(
        text="Facture Atelier Nord numéro 2026-014", duration_seconds=7.0
    )
    return application


def upload(client, content=PDF, filename="facture.pdf", document_type="invoice"):
    return client.post(
        "/extractions",
        files={"file": (filename, content, "application/octet-stream")},
        data={"document_type": document_type},
    )


def test_uploading_a_pdf_returns_a_validated_extraction(app):
    with TestClient(app) as client:
        response = upload(client)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "validated"
    assert body["document_type"] == "invoice"
    assert body["data"]["supplier_name"] == "Atelier Nord"
    assert body["issues"] == []


def test_the_uploaded_file_is_stored_on_disk(app, tmp_path):
    with TestClient(app) as client:
        body = upload(client).json()

    stored = tmp_path / "uploads" / f"{body['document_id']}.pdf"
    assert stored.read_bytes() == PDF


def test_an_extraction_can_be_read_back(app):
    with TestClient(app) as client:
        created = upload(client).json()
        response = client.get(f"/extractions/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_an_unknown_extraction_gives_404(app):
    with TestClient(app) as client:
        assert client.get("/extractions/999").status_code == 404


def test_a_png_is_accepted(app):
    with TestClient(app) as client:
        response = upload(client, content=b"\x89PNG\r\n\x1a\n....", filename="scan.png")

    assert response.status_code == 200


def test_the_real_file_type_matters_not_the_filename(app):
    with TestClient(app) as client:
        response = upload(client, content=b"ceci n'est pas un pdf", filename="facture.pdf")

    assert response.status_code == 415


def test_a_file_that_is_too_large_gives_413(app, monkeypatch):
    monkeypatch.setattr("app.api.extractions.MAX_UPLOAD_BYTES", 10)

    with TestClient(app) as client:
        response = upload(client, content=b"%PDF-1.4 " + b"x" * 100)

    assert response.status_code == 413


def test_an_unknown_document_type_gives_422(app):
    with TestClient(app) as client:
        assert upload(client, document_type="contract").status_code == 422


def test_uploading_a_recording_returns_the_extraction_with_its_transcript(app):
    with TestClient(app) as client:
        response = upload(client, content=WAV, filename="dictee.wav")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "validated"
    assert body["data"]["supplier_name"] == "Atelier Nord"
    assert body["transcript"] == {
        "text": "Facture Atelier Nord numéro 2026-014",
        "language": "fr",
        "duration_seconds": 7.0,
        "model": "fake",
    }


def test_the_transcript_is_returned_when_the_extraction_is_read_back(app):
    with TestClient(app) as client:
        created = upload(client, content=WAV, filename="dictee.wav").json()
        response = client.get(f"/extractions/{created['id']}")

    assert response.json() == created


def test_a_recording_is_stored_with_its_audio_extension(app, tmp_path):
    with TestClient(app) as client:
        body = upload(client, content=WAV, filename="dictee.wav").json()

    assert (tmp_path / "uploads" / f"{body['document_id']}.wav").read_bytes() == WAV


def test_a_pdf_has_no_transcript(app):
    with TestClient(app) as client:
        assert upload(client).json()["transcript"] is None


def test_a_recording_without_speech_gives_502(app):
    app.dependency_overrides[get_transcriber] = lambda: FakeTranscriber(text="")

    with TestClient(app) as client:
        response = upload(client, content=WAV, filename="silence.wav")

    assert response.status_code == 502
    assert "Aucune parole" in response.json()["detail"]
