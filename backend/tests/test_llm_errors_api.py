import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_llm_provider
from app.domains.llm.errors import (
    LLMAuthenticationError,
    LLMRateLimitedError,
    LLMRequestRejectedError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.main import create_app


class RaisingProvider:
    name = "raising"

    def __init__(self, error):
        self.error = error

    def complete(self, request):
        raise self.error


def post_with(tmp_path, monkeypatch, error):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: RaisingProvider(error)
    with TestClient(app) as client:
        return client.post("/llm/complete", json={"task": "simple", "prompt": "Salut"})


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (LLMRateLimitedError("x"), 503),
        (LLMUnavailableError("x"), 502),
        (LLMTimeoutError("x"), 504),
        (LLMAuthenticationError("x"), 503),
        (LLMRequestRejectedError("x"), 502),
    ],
)
def test_a_provider_failure_becomes_a_clean_http_error(tmp_path, monkeypatch, error, status):
    response = post_with(tmp_path, monkeypatch, error)

    assert response.status_code == status
    assert response.json()["detail"]


def test_the_message_is_in_french_and_hides_technical_details(tmp_path, monkeypatch):
    response = post_with(tmp_path, monkeypatch, LLMUnavailableError("httpx.ConnectError 10.0.0.1"))

    assert "10.0.0.1" not in response.json()["detail"]
    assert "modèle" in response.json()["detail"]


def test_a_known_retry_delay_is_forwarded_to_the_client(tmp_path, monkeypatch):
    response = post_with(tmp_path, monkeypatch, LLMRateLimitedError("x", retry_after=7.0))

    assert response.headers["retry-after"] == "7"
