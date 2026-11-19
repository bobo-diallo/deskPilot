import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_embedder
from app.domains.search.embedders.fake import FakeEmbedder
from app.main import create_app

CONTRACT = """Article 1. Paiement sous trente jours fin de mois.

Article 2. Préavis de résiliation de deux mois."""


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    application = create_app()
    application.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    with TestClient(application) as test_client:
        yield test_client


def index(client, title="Contrat Atelier Nord", text=CONTRACT):
    return client.post("/search/documents", json={"title": title, "text": text})


def test_indexing_a_text_reports_how_many_chunks_were_created(client):
    response = index(client)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Contrat Atelier Nord"
    assert body["chunks"] == 2
    assert body["document_id"] > 0


def test_an_empty_text_gives_422(client):
    assert index(client, text="   ").status_code == 422


def test_a_search_returns_the_best_chunks_with_their_source(client):
    index(client)

    response = client.get("/search", params={"q": "préavis de résiliation", "k": 1})

    assert response.status_code == 200
    hit = response.json()[0]
    assert hit["title"] == "Contrat Atelier Nord"
    assert hit["text"] == "Article 2. Préavis de résiliation de deux mois."
    assert hit["score"] > 0


def test_the_mode_can_be_chosen(client):
    index(client)

    response = client.get("/search", params={"q": "paiement", "mode": "keyword"})

    assert response.status_code == 200
    assert response.json()[0]["text"].startswith("Article 1")


def test_an_unknown_mode_gives_422(client):
    assert client.get("/search", params={"q": "x", "mode": "magique"}).status_code == 422


def test_k_must_be_between_1_and_20(client):
    assert client.get("/search", params={"q": "x", "k": 0}).status_code == 422
    assert client.get("/search", params={"q": "x", "k": 21}).status_code == 422


def test_a_question_is_required(client):
    assert client.get("/search").status_code == 422
