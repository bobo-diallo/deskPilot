import os
from types import SimpleNamespace

import pytest

from app.domains.llm.errors import LLMRefusedError
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.schemas import LLMMessage, LLMRequest


class StubMessages:
    """Imite client.messages : garde les paramètres reçus et renvoie une réponse préparée."""

    def __init__(self, reply):
        self.reply = reply
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.reply


def make_client(stop_reason="end_turn", blocks=None):
    blocks = blocks if blocks is not None else [SimpleNamespace(type="text", text="Bonjour !")]
    reply = SimpleNamespace(
        content=blocks,
        stop_reason=stop_reason,
        model="claude-haiku-5-5",
        usage=SimpleNamespace(input_tokens=12, output_tokens=4),
    )
    return SimpleNamespace(messages=StubMessages(reply))


def make_request() -> LLMRequest:
    return LLMRequest(
        model="claude-haiku-5-5",
        system="Tu es utile.",
        messages=[LLMMessage(role="user", content="Salut")],
        max_tokens=200,
    )


def test_request_is_translated_to_the_anthropic_format():
    client = make_client()

    AnthropicProvider(client).complete(make_request())

    assert client.messages.kwargs == {
        "model": "claude-haiku-5-5",
        "max_tokens": 200,
        "system": "Tu es utile.",
        "messages": [{"role": "user", "content": "Salut"}],
    }


def test_response_text_and_tokens_are_extracted():
    response = AnthropicProvider(make_client()).complete(make_request())

    assert response.text == "Bonjour !"
    assert (response.input_tokens, response.output_tokens) == (12, 4)


def test_system_is_omitted_when_not_given():
    client = make_client()
    request = LLMRequest(model="claude-haiku-5-5", messages=[LLMMessage("user", "Salut")])

    AnthropicProvider(client).complete(request)

    assert "system" not in client.messages.kwargs


def test_non_text_blocks_are_ignored():
    blocks = [SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text="Réponse")]

    response = AnthropicProvider(make_client(blocks=blocks)).complete(make_request())

    assert response.text == "Réponse"


def test_a_refusal_raises_a_clear_error():
    with pytest.raises(LLMRefusedError):
        AnthropicProvider(make_client(stop_reason="refusal", blocks=[])).complete(make_request())


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY absente")
def test_real_call_to_anthropic():
    request = LLMRequest(
        model="claude-haiku-5-5",
        messages=[LLMMessage("user", "Réponds uniquement par le mot : pong")],
        max_tokens=300,
    )

    response = AnthropicProvider().complete(request)

    assert "pong" in response.text.lower()
    assert response.input_tokens > 0
