import pytest
from sqlalchemy import select

from app.domains.llm.models import ApiCall
from app.domains.llm.pricing import UnknownModelError
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.router import Task
from app.domains.llm.schemas import LLMMessage, LLMRequest
from app.domains.llm.service import LLMService


def make_request(model: str = "claude-haiku-5-5") -> LLMRequest:
    return LLMRequest(model=model, messages=[LLMMessage(role="user", content="Bonjour")])


def test_complete_returns_the_provider_response(session):
    service = LLMService(FakeProvider(reply="Salut !"), session)

    response = service.complete(make_request())

    assert response.text == "Salut !"


def test_complete_records_one_api_call_with_cost(session):
    provider = FakeProvider(input_tokens=1_000, output_tokens=500)
    service = LLMService(provider, session)

    service.complete(make_request("claude-haiku-5-5"))

    calls = session.scalars(select(ApiCall)).all()
    assert len(calls) == 1
    call = calls[0]
    assert call.provider == "fake"
    assert call.model == "claude-haiku-5-5"
    assert (call.input_tokens, call.output_tokens) == (1_000, 500)
    assert call.cost_usd == pytest.approx(0.00035)
    assert call.latency_ms >= 0


def test_unknown_model_is_not_recorded_with_a_zero_cost(session):
    service = LLMService(FakeProvider(), session)

    with pytest.raises(UnknownModelError):
        service.complete(make_request("claude-inconnu"))

    assert session.scalars(select(ApiCall)).all() == []


def test_the_task_of_the_request_is_recorded_in_the_journal(session):
    service = LLMService(FakeProvider(), session)
    request = LLMRequest(
        model="claude-haiku-5-5",
        messages=[LLMMessage(role="user", content="Bonjour")],
        task=Task.AGENT,
    )

    service.complete(request)

    assert session.scalars(select(ApiCall)).one().task == "agent"


def test_a_request_without_task_is_recorded_with_no_task(session):
    LLMService(FakeProvider(), session).complete(make_request())

    assert session.scalars(select(ApiCall)).one().task is None
