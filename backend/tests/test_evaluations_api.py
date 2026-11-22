import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "2026-11-17-prompt-v2.md").write_text(
        "# Titre\n\nIntro.\n\n## Résumé\n\n| A | B |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8"
    )
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("EVALUATION_REPORTS_DIR", str(reports))
    with TestClient(create_app()) as test_client:
        yield test_client


def test_list_reports(client):
    response = client.get("/evaluations/reports")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "2026-11-17-prompt-v2", "title": "Titre", "date": "2026-11-17"}
    ]


def test_get_report(client):
    body = client.get("/evaluations/reports/2026-11-17-prompt-v2").json()

    assert body["intro"] == "Intro."
    assert body["note"] == ""
    assert body["sections"][0]["tables"][0] == {"headers": ["A", "B"], "rows": [["1", "2"]]}


def test_unknown_report_is_a_404(client):
    assert client.get("/evaluations/reports/inconnu").status_code == 404


def test_path_traversal_is_a_404(client):
    assert client.get("/evaluations/reports/..%2F..%2Fetc%2Fpasswd").status_code == 404
