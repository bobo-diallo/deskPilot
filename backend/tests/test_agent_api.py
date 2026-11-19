import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_embedder, get_llm_provider
from app.domains.llm.providers.fake import ScriptedProvider
from app.domains.search.embedders.fake import FakeEmbedder
from app.main import create_app
from tests.agent.test_agent_service import answer, ask_tools


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORTS_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    application = create_app()
    application.dependency_overrides[get_embedder] = lambda: FakeEmbedder()

    def use_script(*responses):
        provider = ScriptedProvider(list(responses))
        application.dependency_overrides[get_llm_provider] = lambda: provider
        return provider

    return application, use_script, tmp_path


def test_a_question_that_uses_a_tool_returns_the_answer_and_the_trace(setup):
    application, use_script, _ = setup
    use_script(
        ask_tools(("t1", "search_documents", {"query": "préavis"})),
        answer("Le préavis est d'un mois (Contrat Garage Tremblay)."),
    )
    with TestClient(application) as client:
        client.post(
            "/search/documents",
            json={"title": "Contrat Garage Tremblay", "text": "Préavis de résiliation d'un mois."},
        )

        response = client.post("/agent/ask", json={"question": "Quel est le préavis ?"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["answer"] == "Le préavis est d'un mois (Contrat Garage Tremblay)."
    assert [(s["tool_name"], s["status"]) for s in body["steps"]] == [
        ("search_documents", "executed")
    ]
    assert "Garage Tremblay" in body["steps"][0]["result"]
    assert body["pending_tool"] is None


def test_an_export_request_waits_for_approval_and_writes_nothing(setup):
    application, use_script, tmp_path = setup
    use_script(ask_tools(("t1", "export_invoices", {"extraction_ids": [1]})))
    with TestClient(application) as client:
        response = client.post("/agent/ask", json={"question": "Exporte la facture 1"})

    body = response.json()
    assert body["status"] == "awaiting_approval"
    assert body["pending_tool"] == {"name": "export_invoices", "arguments": {"extraction_ids": [1]}}
    assert not (tmp_path / "exports").exists()  # aucune exécution sans approbation


def test_approving_resumes_the_run_until_the_final_answer(setup):
    application, use_script, _ = setup
    use_script(
        ask_tools(("t1", "export_invoices", {"extraction_ids": [999]})),
        answer("Je n'ai pas trouvé cette facture."),
    )
    with TestClient(application) as client:
        run_id = client.post("/agent/ask", json={"question": "Exporte"}).json()["id"]

        response = client.post(f"/agent/runs/{run_id}/approve")

    body = response.json()
    assert response.status_code == 200 and body["status"] == "completed"
    # L'outil a été exécuté après approbation et a échoué proprement (facture inconnue)
    assert body["steps"][0]["status"] == "error"
    assert body["answer"] == "Je n'ai pas trouvé cette facture."


def test_rejecting_resumes_the_run_without_executing_the_tool(setup):
    application, use_script, tmp_path = setup
    use_script(
        ask_tools(("t1", "export_invoices", {"extraction_ids": [1]})),
        answer("D'accord, rien exporté."),
    )
    with TestClient(application) as client:
        run_id = client.post("/agent/ask", json={"question": "Exporte"}).json()["id"]

        body = client.post(f"/agent/runs/{run_id}/reject").json()

    assert body["status"] == "completed"
    assert body["steps"][0]["status"] == "rejected"
    assert not (tmp_path / "exports").exists()


def test_a_run_can_be_read_back(setup):
    application, use_script, _ = setup
    use_script(answer("Bonjour !"))
    with TestClient(application) as client:
        created = client.post("/agent/ask", json={"question": "Bonjour"}).json()

        response = client.get(f"/agent/runs/{created['id']}")

    assert response.status_code == 200 and response.json() == created


def test_unknown_run_gives_404_and_wrong_state_gives_409(setup):
    application, use_script, _ = setup
    use_script(answer("Bonjour !"))
    with TestClient(application) as client:
        assert client.get("/agent/runs/999").status_code == 404
        assert client.post("/agent/runs/999/approve").status_code == 404
        run_id = client.post("/agent/ask", json={"question": "Bonjour"}).json()["id"]
        assert client.post(f"/agent/runs/{run_id}/approve").status_code == 409


def test_an_empty_question_gives_422(setup):
    application, use_script, _ = setup
    use_script()
    with TestClient(application) as client:
        assert client.post("/agent/ask", json={"question": ""}).status_code == 422


def test_without_an_api_key_the_agent_gives_503(setup):
    application, _, _ = setup  # pas de surcharge du fournisseur : on utilise le vrai, sans clé
    with TestClient(application) as client:
        assert client.post("/agent/ask", json={"question": "Bonjour"}).status_code == 503
