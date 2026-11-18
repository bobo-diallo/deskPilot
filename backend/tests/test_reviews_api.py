from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_llm_provider, get_transcriber
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.llm.providers.fake import FakeProvider
from app.domains.transcription.transcribers.fake import FakeTranscriber
from app.main import create_app

WAV = b"RIFF\x24\x00\x00\x00WAVEfmt fausse dictee"


def make_invoice(**changes) -> Invoice:
    values = dict(
        supplier_name="Plomberie Tremblée",
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


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    application = create_app()
    application.dependency_overrides[get_llm_provider] = lambda: FakeProvider(parsed=make_invoice())
    application.dependency_overrides[get_transcriber] = lambda: FakeTranscriber(text="Facture")
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def dictate(client) -> int:
    """Dépose une dictée : l'extraction obtenue est à relire. Renvoie son identifiant."""
    response = client.post(
        "/extractions",
        files={"file": ("dictee.wav", WAV, "application/octet-stream")},
        data={"document_type": "invoice"},
    )
    assert response.json()["status"] == "needs_review"
    return response.json()["id"]


def test_the_queue_lists_extractions_waiting_for_review_with_their_transcript(client):
    extraction_id = dictate(client)

    response = client.get("/reviews")

    assert response.status_code == 200
    items = response.json()
    assert [item["id"] for item in items] == [extraction_id]
    assert items[0]["transcript"]["text"] == "Facture"


def test_approving_removes_the_extraction_from_the_queue(client):
    extraction_id = dictate(client)

    response = client.post(f"/reviews/{extraction_id}/approve", json={"comment": "ok"})

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert client.get("/reviews").json() == []


def test_correcting_returns_the_corrected_extraction(client):
    extraction_id = dictate(client)
    corrected = make_invoice(supplier_name="Plomberie Tremblay").model_dump(mode="json")

    response = client.post(f"/reviews/{extraction_id}/correct", json={"data": corrected})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "corrected"
    assert body["data"]["supplier_name"] == "Plomberie Tremblay"
    assert body["issues"] == []


def test_rejecting_marks_the_extraction_rejected(client):
    extraction_id = dictate(client)

    response = client.post(f"/reviews/{extraction_id}/reject", json={"comment": "Illisible"})

    assert response.json()["status"] == "rejected"


def test_an_unknown_extraction_gives_404(client):
    assert client.post("/reviews/999/approve", json={}).status_code == 404


def test_reviewing_twice_gives_409(client):
    extraction_id = dictate(client)
    client.post(f"/reviews/{extraction_id}/approve", json={})

    response = client.post(f"/reviews/{extraction_id}/reject", json={})

    assert response.status_code == 409


def test_a_correction_that_changes_nothing_gives_422(client):
    extraction_id = dictate(client)

    response = client.post(
        f"/reviews/{extraction_id}/correct", json={"data": make_invoice().model_dump(mode="json")}
    )

    assert response.status_code == 422
    assert "approuver" in response.json()["detail"]


def test_a_malformed_correction_gives_422(client):
    extraction_id = dictate(client)

    response = client.post(f"/reviews/{extraction_id}/correct", json={"data": {"total": "abc"}})

    assert response.status_code == 422


def test_statistics_summarise_the_decisions(client):
    first, second = dictate(client), dictate(client)
    client.post(f"/reviews/{first}/approve", json={})
    corrected = make_invoice(supplier_name="Tremblay").model_dump(mode="json")
    client.post(f"/reviews/{second}/correct", json={"data": corrected})

    stats = client.get("/reviews/stats").json()

    assert stats == {
        "reviewed": 2,
        "approved": 1,
        "corrected": 1,
        "rejected": 0,
        "correction_rate": 0.5,
        "field_corrections": {"supplier_name": 1},
    }
