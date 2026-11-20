import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with TestClient(create_app()) as test_client:
        yield test_client


def test_the_test_page_is_served_as_html(client):
    response = client.get("/test-page")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_the_test_page_covers_every_feature_of_the_api(client):
    html = client.get("/test-page").text

    # Chaque route utilisée par la page doit exister dans l'API : on vérifie les deux côtés.
    for route in ["/extractions", "/reviews", "/search", "/agent/ask", "/costs/summary"]:
        assert route in html


def test_the_test_page_never_embeds_a_secret(client):
    html = client.get("/test-page").text.lower()

    assert "api_key" not in html and "sk-ant" not in html
