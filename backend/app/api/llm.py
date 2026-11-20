from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_llm_provider
from app.domains.llm.errors import LLMRefusedError
from app.domains.llm.ports import LLMProvider
from app.domains.llm.pricing import compute_cost_usd
from app.domains.llm.router import Task, choose_model
from app.domains.llm.schemas import LLMMessage, LLMRequest
from app.domains.llm.service import LLMService

router = APIRouter(prefix="/llm", tags=["llm"])


class CompleteBody(BaseModel):
    task: Task
    prompt: str
    system: str | None = None


class CompleteResult(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@router.post("/complete")
def complete(
    body: CompleteBody,
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    session: Annotated[Session, Depends(get_db_session)],
) -> CompleteResult:
    request = LLMRequest(
        model=choose_model(body.task),
        task=body.task,
        system=body.system,
        messages=[LLMMessage(role="user", content=body.prompt)],
    )
    try:
        response = LLMService(provider, session).complete(request)
    except LLMRefusedError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return CompleteResult(
        text=response.text,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        cost_usd=compute_cost_usd(response.model, response.input_tokens, response.output_tokens),
    )
