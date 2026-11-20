from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domains.llm.models import ApiCall
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with TestClient(create_app()) as test_client:
        yield test_client


def seed(client, *calls):
    with Session(client.app.state.engine) as session:
        session.add_all(calls)
        session.commit()


def make_call(day: int, *, model="claude-haiku-5-5", task="extraction", cost=0.01, latency=120):
    return ApiCall(
        provider="anthropic",
        model=model,
        task=task,
        input_tokens=1_000,
        output_tokens=200,
        cost_usd=cost,
        latency_ms=latency,
        created_at=datetime(2026, 11, day, 9, 0, tzinfo=UTC),
    )


def test_summary_of_an_empty_journal_is_all_zero(client):
    body = client.get("/costs/summary").json()

    assert body["totals"] == {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    assert body["by_model"] == []
    assert body["by_task"] == []


def test_summary_returns_totals_and_both_breakdowns(client):
    seed(
        client,
        make_call(10, task="extraction", cost=0.01),
        make_call(10, task="agent", cost=0.02, model="claude-sonnet-5-5"),
    )

    body = client.get("/costs/summary").json()

    assert body["totals"]["calls"] == 2
    assert body["totals"]["cost_usd"] == pytest.approx(0.03)
    assert body["by_model"][0]["key"] == "claude-sonnet-5-5"
    assert {row["key"] for row in body["by_task"]} == {"extraction", "agent"}
    assert body["by_task"][0]["latency_p95_ms"] == 120


def test_summary_can_be_limited_to_a_period_with_inclusive_dates(client):
    seed(client, make_call(9, cost=1.0), make_call(10, cost=2.0), make_call(11, cost=4.0))

    body = client.get("/costs/summary", params={"from": "2026-11-10", "to": "2026-11-10"}).json()

    assert body["totals"]["calls"] == 1
    assert body["totals"]["cost_usd"] == pytest.approx(2.0)


def test_daily_returns_one_row_per_day(client):
    seed(client, make_call(10, cost=0.1), make_call(10, cost=0.2), make_call(12, cost=0.3))

    body = client.get("/costs/daily").json()

    assert [(row["day"], row["calls"]) for row in body] == [("2026-11-10", 2), ("2026-11-12", 1)]


def test_an_inverted_period_is_rejected(client):
    response = client.get("/costs/summary", params={"from": "2026-11-12", "to": "2026-11-10"})

    assert response.status_code == 422


def test_a_malformed_date_is_rejected(client):
    assert client.get("/costs/summary", params={"from": "hier"}).status_code == 422
