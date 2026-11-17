from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.schemas import LLMMessage, LLMRequest


def make_request() -> LLMRequest:
    return LLMRequest(
        model="claude-haiku-5-5", messages=[LLMMessage(role="user", content="Bonjour")]
    )


def test_fake_provider_returns_its_canned_reply():
    provider = FakeProvider(reply="Salut !", input_tokens=7, output_tokens=3)

    response = provider.complete(make_request())

    assert response.text == "Salut !"
    assert response.model == "claude-haiku-5-5"
    assert (response.input_tokens, response.output_tokens) == (7, 3)


def test_fake_provider_remembers_the_requests_it_received():
    provider = FakeProvider()
    request = make_request()

    provider.complete(request)

    assert provider.received == [request]


def test_fake_provider_can_return_a_parsed_object():
    provider = FakeProvider(parsed={"city": "Québec"})

    response = provider.complete(make_request())

    assert response.parsed == {"city": "Québec"}
