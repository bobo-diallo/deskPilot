from types import SimpleNamespace

import pytest

from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.providers.fake import ScriptedProvider
from app.domains.llm.schemas import LLMMessage, LLMRequest, LLMResponse, ToolCall, ToolSpec

SEARCH_TOOL = ToolSpec(
    name="search_documents",
    description="Cherche dans les contrats",
    input_schema={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
)


class StubMessages:
    def __init__(self, reply):
        self.reply = reply
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.reply


def make_client(blocks, stop_reason="end_turn"):
    reply = SimpleNamespace(
        content=blocks,
        stop_reason=stop_reason,
        model="claude-haiku-5-5",
        usage=SimpleNamespace(input_tokens=30, output_tokens=12),
    )
    return SimpleNamespace(messages=StubMessages(reply))


def make_request(**changes) -> LLMRequest:
    values = dict(
        model="claude-haiku-5-5",
        messages=[LLMMessage("user", "Quel est le préavis ?")],
        tools=[SEARCH_TOOL],
    )
    values.update(changes)
    return LLMRequest(**values)


def test_tools_are_sent_in_the_anthropic_format():
    client = make_client([SimpleNamespace(type="text", text="ok")])

    AnthropicProvider(client).complete(make_request())

    assert client.messages.kwargs["tools"] == [
        {
            "name": "search_documents",
            "description": "Cherche dans les contrats",
            "input_schema": SEARCH_TOOL.input_schema,
        }
    ]


def test_no_tools_key_is_sent_when_the_request_has_no_tools():
    client = make_client([SimpleNamespace(type="text", text="ok")])

    AnthropicProvider(client).complete(make_request(tools=[]))

    assert "tools" not in client.messages.kwargs


def test_a_tool_use_block_becomes_a_tool_call_and_the_raw_blocks_are_kept():
    block = SimpleNamespace(
        type="tool_use", id="toolu_1", name="search_documents", input={"query": "préavis"}
    )
    client = make_client([SimpleNamespace(type="text", text="Je cherche."), block], "tool_use")

    response = AnthropicProvider(client).complete(make_request())

    assert response.stop_reason == "tool_use"
    assert response.tool_calls == [ToolCall("toolu_1", "search_documents", {"query": "préavis"})]
    assert response.text == "Je cherche."
    # Les blocs bruts servent à rejouer le tour de l'assistant tel quel à l'appel suivant
    assert response.content_blocks[1] == {
        "type": "tool_use",
        "id": "toolu_1",
        "name": "search_documents",
        "input": {"query": "préavis"},
    }


def test_a_plain_answer_has_no_tool_calls():
    response = AnthropicProvider(
        make_client([SimpleNamespace(type="text", text="Deux mois.")])
    ).complete(make_request())

    assert response.tool_calls == []
    assert response.text == "Deux mois."


def test_messages_made_of_blocks_are_passed_through_unchanged():
    client = make_client([SimpleNamespace(type="text", text="ok")])
    tool_result = [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "Deux mois"}]
    messages = [
        LLMMessage("user", "Quel préavis ?"),
        LLMMessage("assistant", [{"type": "tool_use", "id": "toolu_1", "name": "x", "input": {}}]),
        LLMMessage("user", tool_result),
    ]

    AnthropicProvider(client).complete(make_request(messages=messages))

    sent = client.messages.kwargs["messages"]
    assert sent[1]["content"][0]["type"] == "tool_use"
    assert sent[2]["content"] == tool_result


def test_scripted_provider_returns_its_responses_in_order_and_records_requests():
    first = LLMResponse(text="a", model="claude-haiku-5-5", input_tokens=1, output_tokens=1)
    second = LLMResponse(text="b", model="claude-haiku-5-5", input_tokens=1, output_tokens=1)
    provider = ScriptedProvider([first, second])

    assert provider.complete(make_request()).text == "a"
    assert provider.complete(make_request()).text == "b"
    assert len(provider.received) == 2


def test_scripted_provider_fails_loudly_when_the_script_is_exhausted():
    provider = ScriptedProvider([])

    with pytest.raises(AssertionError, match="script"):
        provider.complete(make_request())
