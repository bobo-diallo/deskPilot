from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_agent_service, get_db_session
from app.domains.agent.errors import AgentRunNotFoundError, AgentStateError
from app.domains.agent.models import AgentRun, AgentStep
from app.domains.agent.service import AgentService
from app.domains.llm.errors import LLMInvalidOutputError, LLMRefusedError

router = APIRouter(prefix="/agent", tags=["agent"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class StepResult(BaseModel):
    position: int
    tool_name: str
    arguments: dict
    result: str | None
    status: str


class PendingTool(BaseModel):
    name: str
    arguments: dict


class AgentRunResult(BaseModel):
    id: int
    question: str
    status: str
    answer: str | None
    model: str
    steps_used: int
    steps: list[StepResult]
    pending_tool: PendingTool | None  # l'action sensible qui attend l'approbation, le cas échéant


def _result(session: Session, run: AgentRun) -> AgentRunResult:
    steps = session.scalars(
        select(AgentStep).where(AgentStep.run_id == run.id).order_by(AgentStep.position)
    )
    pending = (
        PendingTool(name=run.pending_calls[0]["name"], arguments=run.pending_calls[0]["arguments"])
        if run.status == "awaiting_approval" and run.pending_calls
        else None
    )
    return AgentRunResult(
        id=run.id,
        question=run.question,
        status=run.status,
        answer=run.answer,
        model=run.model,
        steps_used=run.steps_used,
        steps=[
            StepResult(
                position=s.position,
                tool_name=s.tool_name,
                arguments=s.arguments,
                result=s.result,
                status=s.status,
            )
            for s in steps
        ],
        pending_tool=pending,
    )


def _run_or_http_error(action, session: Session) -> AgentRunResult:
    """Exécute une action de l'agent et traduit les erreurs du domaine en réponses HTTP."""
    try:
        return _result(session, action())
    except AgentRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except AgentStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LLMRefusedError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LLMInvalidOutputError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/ask")
def ask(
    body: AskRequest,
    agent: Annotated[AgentService, Depends(get_agent_service)],
    session: Annotated[Session, Depends(get_db_session)],
) -> AgentRunResult:
    return _run_or_http_error(lambda: agent.ask(body.question), session)


@router.get("/runs/{run_id}")
def get_run(run_id: int, session: Annotated[Session, Depends(get_db_session)]) -> AgentRunResult:
    run = session.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Exécution {run_id} introuvable")
    return _result(session, run)


@router.post("/runs/{run_id}/approve")
def approve(
    run_id: int,
    agent: Annotated[AgentService, Depends(get_agent_service)],
    session: Annotated[Session, Depends(get_db_session)],
) -> AgentRunResult:
    return _run_or_http_error(lambda: agent.approve(run_id), session)


@router.post("/runs/{run_id}/reject")
def reject(
    run_id: int,
    agent: Annotated[AgentService, Depends(get_agent_service)],
    session: Annotated[Session, Depends(get_db_session)],
) -> AgentRunResult:
    return _run_or_http_error(lambda: agent.reject(run_id), session)
