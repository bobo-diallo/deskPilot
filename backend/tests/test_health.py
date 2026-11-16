from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_creates_database_tables(tmp_path, monkeypatch):
    database_file = tmp_path / "startup.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file}")

    with TestClient(create_app()):
        pass

    assert database_file.exists()
