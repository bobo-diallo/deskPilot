import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import init_database
from app.domains.agent.models import AgentStep
from app.domains.agent.registry import build_registry
from app.domains.agent.service import AgentService
from app.domains.llm.models import ApiCall
from app.domains.llm.ports import LLMProvider
from app.domains.llm.service import LLMService
from app.domains.search.ports import Embedder
from app.evaluation.agent_dataset import AgentDataset, AgentQuestion
from app.evaluation.agent_judge import judge
from app.evaluation.agent_world import build_world


@dataclass(frozen=True)
class TrialResult:
    """Une question posée une fois à l'agent, avec ce qu'il a fait et ce que ça a coûté."""

    question_id: str
    tags: tuple[str, ...]
    run: int
    success: bool
    failures: list[str]
    unsafe: bool
    tools: list[str]  # outils demandés, dans l'ordre
    steps_used: int  # appels au modèle
    status: str
    answer: str | None
    cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: int
    error: str | None


@dataclass(frozen=True)
class VariantResult:
    name: str
    model: str
    trials: list[TrialResult]


def run_agent_variant(
    name: str,
    model: str,
    provider: LLMProvider,
    dataset: AgentDataset,
    embedder: Embedder,
    runs: int = 1,
    questions: list[AgentQuestion] | None = None,
) -> VariantResult:
    """Pose chaque question `runs` fois à un agent, dans un monde neuf en mémoire.

    Rien n'est jamais approuvé : une action sensible demandée reste en attente, ce qui suffit à
    mesurer ce que l'agent voulait faire sans rien exécuter. Les coûts viennent du journal
    `api_calls`, comme pour les autres évaluations.
    """
    trials: list[TrialResult] = []
    engine = create_engine("sqlite://")
    init_database(engine)
    with Session(engine) as session, tempfile.TemporaryDirectory() as export_dir:
        build_world(session, dataset, embedder)
        llm = LLMService(provider, session)
        registry = build_registry(session, embedder, Path(export_dir))

        for question in questions if questions is not None else dataset.questions:
            for run in range(1, runs + 1):
                last_id = session.scalar(select(func.coalesce(func.max(ApiCall.id), 0)))
                started = time.perf_counter()
                agent_run, error = None, None
                try:
                    agent_run = AgentService(llm, registry, session, model).ask(question.question)
                except (
                    Exception
                ) as exc:  # noqa: BLE001 - un essai raté ne doit pas arrêter la mesure
                    error = f"{type(exc).__name__}: {exc}"
                latency_ms = round((time.perf_counter() - started) * 1000)

                calls = session.scalars(select(ApiCall).where(ApiCall.id > last_id)).all()
                tools = (
                    list(
                        session.scalars(
                            select(AgentStep.tool_name)
                            .where(AgentStep.run_id == agent_run.id)
                            .order_by(AgentStep.position)
                        )
                    )
                    if agent_run
                    else []
                )
                status = agent_run.status if agent_run else "error"
                answer = agent_run.answer if agent_run else None
                verdict = judge(question, status, tools, answer)
                trials.append(
                    TrialResult(
                        question_id=question.id,
                        tags=question.tags,
                        run=run,
                        success=verdict.success and error is None,
                        failures=verdict.failures,
                        unsafe=verdict.unsafe,
                        tools=tools,
                        steps_used=agent_run.steps_used if agent_run else 0,
                        status=status,
                        answer=answer,
                        cost_usd=sum(c.cost_usd for c in calls),
                        input_tokens=sum(c.input_tokens for c in calls),
                        output_tokens=sum(c.output_tokens for c in calls),
                        latency_ms=latency_ms,
                        error=error,
                    )
                )
    return VariantResult(name=name, model=model, trials=trials)
