import pytest

from app.domains.agent.prompts import AGENT_PROMPTS
from app.domains.agent.service import AgentService
from app.domains.agent.tools.base import ToolRegistry
from app.domains.llm.providers.fake import ScriptedProvider
from app.domains.llm.service import LLMService
from tests.agent.test_agent_service import (
    BoomTool,
    Recorder,
    UpperTool,
    WipeTool,
    answer,
    ask_tools,
    build,
)


@pytest.fixture
def recorder():
    return Recorder()


def test_a_run_remembers_the_prompt_version_it_used(session, recorder):
    provider, service = build(session, recorder, [answer()])

    run = service.ask("Bonjour")

    assert run.prompt_version == AGENT_PROMPTS.default
    assert provider.received[0].system == AGENT_PROMPTS.get(AGENT_PROMPTS.default)


def test_a_run_resumed_after_approval_keeps_its_original_prompt(session, recorder, monkeypatch):
    # Une version plus récente devient le défaut entre la question et l'approbation.
    monkeypatch.setitem(AGENT_PROMPTS.versions, "v0-test", "Ancien prompt de test")
    registry = ToolRegistry([UpperTool(recorder), BoomTool(), WipeTool(recorder)])
    first = AgentService(
        LLMService(ScriptedProvider([ask_tools(("t1", "wipe", {"word": "x"}))]), session),
        registry,
        session,
        model="claude-haiku-5-5",
        prompt_version="v0-test",
    )
    paused = first.ask("Efface x")
    assert paused.status == "awaiting_approval"

    later_provider = ScriptedProvider([answer("Fait.")])
    later = AgentService(
        LLMService(later_provider, session), registry, session, model="claude-haiku-5-5"
    )
    later.approve(paused.id)

    assert later_provider.received[0].system == "Ancien prompt de test"


def test_an_unknown_prompt_version_is_refused_at_construction(session, recorder):
    with pytest.raises(ValueError, match="v99"):
        AgentService(
            LLMService(ScriptedProvider([]), session),
            ToolRegistry([]),
            session,
            model="claude-haiku-5-5",
            prompt_version="v99",
        )
