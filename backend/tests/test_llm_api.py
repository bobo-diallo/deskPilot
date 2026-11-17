import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_llm_provider
from app.domains.llm.errors import LLMRefusedError
from app.domains.llm.models import ApiCall
from app.domains.llm.providers.fake import FakeProvider
from app.main import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    return create_app()


def test_complete_returns_text_model_and_cost(app):
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(
        reply="Voici", input_tokens=1_000, output_tokens=500
    )

    with TestClient(app) as client:
        response = client.post("/llm/complete", json={"task": "simple", "prompt": "Bonjour"})

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Voici"
    assert body["model"] == "claude-haiku-5-5"
    assert body["cost_usd"] == pytest.approx(0.00035)


def test_extraction_task_is_routed_to_the_stronger_model(app):
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()

    with TestClient(app) as client:
        response = client.post("/llm/complete", json={"task": "extraction", "prompt": "Facture"})

    assert response.json()["model"] == "claude-sonnet-5-5"


def test_call_is_recorded_in_the_cost_journal(app):
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()

    with TestClient(app) as client:
        client.post("/llm/complete", json={"task": "simple", "prompt": "Bonjour"})
        with Session(app.state.engine) as session:
            assert len(session.scalars(select(ApiCall)).all()) == 1


def test_missing_api_key_gives_a_clear_503(app):
    with TestClient(app) as client:
        response = client.post("/llm/complete", json={"task": "simple", "prompt": "Bonjour"})

    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_refusal_gives_a_422(app):
    class RefusingProvider(FakeProvider):
        def complete(self, request):
            raise LLMRefusedError("refusé")

    app.dependency_overrides[get_llm_provider] = lambda: RefusingProvider()

    with TestClient(app) as client:
        response = client.post("/llm/complete", json={"task": "simple", "prompt": "Bonjour"})

    assert response.status_code == 422
