import pytest
from pydantic import BaseModel
from sqlalchemy import select

from app.domains.agent.errors import AgentRunNotFoundError, AgentStateError
from app.domains.agent.models import AgentStep
from app.domains.agent.service import SYSTEM_PROMPT, AgentService
from app.domains.agent.tools.base import Tool, ToolExecutionError, ToolRegistry
from app.domains.llm.providers.fake import ScriptedProvider
from app.domains.llm.schemas import LLMResponse, ToolCall
from app.domains.llm.service import LLMService


class WordArgs(BaseModel):
    word: str


class Recorder:
    """Note chaque exécution réelle d'un outil (preuve qu'une action sensible n'a pas eu lieu)."""

    def __init__(self):
        self.executed: list[str] = []


class UpperTool(Tool):
    name = "upper"
    description = "Met en majuscules"
    args_model = WordArgs

    def __init__(self, recorder: Recorder):
        self._recorder = recorder

    def run(self, arguments: WordArgs) -> str:
        self._recorder.executed.append(f"upper:{arguments.word}")
        return arguments.word.upper()


class BoomTool(Tool):
    name = "boom"
    description = "Échoue toujours"
    args_model = WordArgs

    def run(self, arguments: WordArgs) -> str:
        raise ToolExecutionError("Facture introuvable")


class WipeTool(Tool):
    name = "wipe"
    description = "Action sensible"
    args_model = WordArgs
    sensitive = True

    def __init__(self, recorder: Recorder):
        self._recorder = recorder

    def run(self, arguments: WordArgs) -> str:
        self._recorder.executed.append(f"wipe:{arguments.word}")
        return "effacé"


def answer(text="Voici la réponse.") -> LLMResponse:
    return LLMResponse(
        text=text,
        model="claude-haiku-5-5",
        input_tokens=100,
        output_tokens=20,
        content_blocks=[{"type": "text", "text": text}],
        stop_reason="end_turn",
    )


def ask_tools(*calls: tuple[str, str, dict]) -> LLMResponse:
    """Réponse du modèle qui demande des outils : (id, nom, arguments)."""
    tool_calls = [ToolCall(i, n, a) for i, n, a in calls]
    return LLMResponse(
        text="",
        model="claude-haiku-5-5",
        input_tokens=100,
        output_tokens=20,
        tool_calls=tool_calls,
        content_blocks=[{"type": "tool_use", "id": i, "name": n, "input": a} for i, n, a in calls],
        stop_reason="tool_use",
    )


@pytest.fixture
def recorder():
    return Recorder()


def build(session, recorder, script, max_steps=6):
    provider = ScriptedProvider(script)
    registry = ToolRegistry([UpperTool(recorder), BoomTool(), WipeTool(recorder)])
    service = AgentService(
        LLMService(provider, session), registry, session, model="claude-haiku-5-5",
        max_steps=max_steps,
    )  # fmt: skip
    return provider, service


def last_tool_results(provider) -> list[dict]:
    return provider.received[-1].messages[-1].content


def test_a_question_that_needs_no_tool_is_answered_directly(session, recorder):
    provider, service = build(session, recorder, [answer("Bonjour !")])

    run = service.ask("Bonjour")

    assert (run.status, run.answer, run.steps_used) == ("completed", "Bonjour !", 1)
    assert provider.received[0].messages[0].content == "Bonjour"


def test_every_request_carries_the_system_prompt_and_the_tools(session, recorder):
    provider, service = build(session, recorder, [answer()])

    service.ask("Bonjour")

    request = provider.received[0]
    assert request.system == SYSTEM_PROMPT
    assert [tool.name for tool in request.tools] == ["upper", "boom", "wipe"]


def test_the_system_prompt_tells_the_model_to_treat_documents_as_data(session, recorder):
    assert "jamais" in SYSTEM_PROMPT and "instruction" in SYSTEM_PROMPT
    assert "export_invoices" in SYSTEM_PROMPT


def test_a_tool_is_executed_and_its_result_goes_back_to_the_model(session, recorder):
    script = [ask_tools(("t1", "upper", {"word": "abc"})), answer("C'est ABC.")]
    provider, service = build(session, recorder, script)

    run = service.ask("Mets abc en majuscules")

    assert run.status == "completed" and run.answer == "C'est ABC." and run.steps_used == 2
    assert recorder.executed == ["upper:abc"]
    second_call = provider.received[1].messages
    assert second_call[1].role == "assistant"
    assert second_call[1].content[0]["type"] == "tool_use"
    assert second_call[2].role == "user"
    assert second_call[2].content == [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ABC", "is_error": False}
    ]


def test_invalid_arguments_are_given_back_to_the_model_as_an_error(session, recorder):
    script = [ask_tools(("t1", "upper", {"mot": "abc"})), answer("Désolé.")]
    provider, service = build(session, recorder, script)

    run = service.ask("x")

    result = last_tool_results(provider)[0]
    assert result["is_error"] is True and "Arguments" in result["content"]
    assert recorder.executed == []  # rien d'exécuté avec des arguments invalides
    assert run.status == "completed"


def test_an_unknown_tool_is_given_back_as_an_error(session, recorder):
    script = [ask_tools(("t1", "format_disk", {})), answer("Impossible.")]
    provider, service = build(session, recorder, script)

    service.ask("x")

    assert last_tool_results(provider)[0]["is_error"] is True
    assert "inconnu" in last_tool_results(provider)[0]["content"]


def test_a_tool_error_is_given_back_so_the_model_can_adapt(session, recorder):
    script = [ask_tools(("t1", "boom", {"word": "x"})), answer("Cette facture n'existe pas.")]
    provider, service = build(session, recorder, script)

    run = service.ask("x")

    assert last_tool_results(provider)[0] == {
        "type": "tool_result",
        "tool_use_id": "t1",
        "content": "Facture introuvable",
        "is_error": True,
    }
    assert run.answer == "Cette facture n'existe pas."


def test_the_number_of_steps_is_limited(session, recorder):
    endless = [ask_tools((f"t{n}", "upper", {"word": "a"})) for n in range(10)]
    provider, service = build(session, recorder, endless, max_steps=3)

    run = service.ask("boucle")

    assert run.status == "step_limit"
    assert "3" in run.answer
    assert len(provider.received) == 3  # jamais plus d'appels au modèle que la limite


def test_the_trace_records_each_tool_call_in_order(session, recorder):
    script = [
        ask_tools(("t1", "upper", {"word": "a"}), ("t2", "boom", {"word": "b"})),
        answer(),
    ]
    _, service = build(session, recorder, script)

    run = service.ask("x")

    steps = session.scalars(select(AgentStep).order_by(AgentStep.position)).all()
    assert [(s.run_id, s.position, s.tool_name, s.status) for s in steps] == [
        (run.id, 1, "upper", "executed"),
        (run.id, 2, "boom", "error"),
    ]
    assert steps[0].arguments == {"word": "a"} and steps[0].result == "A"


# --- actions sensibles ------------------------------------------------------------------------


def test_a_sensitive_tool_is_never_executed_without_approval(session, recorder):
    script = [ask_tools(("t1", "wipe", {"word": "tout"}))]
    provider, service = build(session, recorder, script)

    run = service.ask("Efface tout")

    assert run.status == "awaiting_approval"
    assert recorder.executed == []  # LA garantie : rien n'a été exécuté
    assert run.pending_calls[0]["name"] == "wipe"
    assert len(provider.received) == 1  # le modèle n'est pas rappelé tant qu'on attend l'humain
    step = session.scalars(select(AgentStep)).one()
    assert step.status == "awaiting_approval"


def test_approving_executes_the_action_and_the_agent_finishes(session, recorder):
    script = [ask_tools(("t1", "wipe", {"word": "tout"})), answer("Fait.")]
    provider, service = build(session, recorder, script)
    run = service.ask("Efface tout")

    run = service.approve(run.id)

    assert recorder.executed == ["wipe:tout"]
    assert (run.status, run.answer) == ("completed", "Fait.")
    assert last_tool_results(provider)[0]["content"] == "effacé"
    assert session.scalars(select(AgentStep)).one().status == "executed"


def test_rejecting_tells_the_model_the_human_refused_and_executes_nothing(session, recorder):
    script = [ask_tools(("t1", "wipe", {"word": "tout"})), answer("Compris, je n'efface rien.")]
    provider, service = build(session, recorder, script)
    run = service.ask("Efface tout")

    run = service.reject(run.id)

    assert recorder.executed == []
    result = last_tool_results(provider)[0]
    assert result["is_error"] is True and "refus" in result["content"]
    assert run.status == "completed"
    assert session.scalars(select(AgentStep)).one().status == "rejected"


def test_calls_around_a_sensitive_one_keep_their_order_and_pair_up_in_one_message(
    session, recorder
):
    script = [
        ask_tools(
            ("t1", "upper", {"word": "a"}),
            ("t2", "wipe", {"word": "b"}),
            ("t3", "upper", {"word": "c"}),
        ),
        answer("Terminé."),
    ]
    provider, service = build(session, recorder, script)
    run = service.ask("x")

    assert run.status == "awaiting_approval"
    assert recorder.executed == ["upper:a"]  # t1 passe, t2 attend, t3 n'est pas encore lancé

    service.approve(run.id)

    assert recorder.executed == ["upper:a", "wipe:b", "upper:c"]
    results = last_tool_results(provider)
    assert [r["tool_use_id"] for r in results] == [
        "t1",
        "t2",
        "t3",
    ]  # l'API exige tous les résultats


def test_a_run_can_only_be_decided_while_it_awaits_approval(session, recorder):
    _, service = build(session, recorder, [answer()])
    run = service.ask("Bonjour")

    with pytest.raises(AgentStateError):
        service.approve(run.id)
    with pytest.raises(AgentStateError):
        service.reject(run.id)


def test_an_unknown_run_is_reported(session, recorder):
    _, service = build(session, recorder, [])

    with pytest.raises(AgentRunNotFoundError):
        service.approve(999)


def test_a_sensitive_call_after_approval_can_pause_again(session, recorder):
    script = [
        ask_tools(("t1", "wipe", {"word": "a"})),
        ask_tools(("t2", "wipe", {"word": "b"})),
        answer("Fini."),
    ]
    _, service = build(session, recorder, script)
    run = service.ask("x")

    run = service.approve(run.id)

    assert run.status == "awaiting_approval"  # la deuxième action sensible attend à son tour
    assert recorder.executed == ["wipe:a"]
    run = service.approve(run.id)
    assert run.status == "completed" and recorder.executed == ["wipe:a", "wipe:b"]
