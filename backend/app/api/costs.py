from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.domains.costs.service import CostService, Period

router = APIRouter(prefix="/costs", tags=["costs"])


class TotalsResult(BaseModel):
    calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float


class BreakdownResult(BaseModel):
    key: str | None  # null : appels sans tâche enregistrée (avant la story 06a)
    calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_p50_ms: int
    latency_p95_ms: int


class SummaryResult(BaseModel):
    totals: TotalsResult
    by_model: list[BreakdownResult]
    by_task: list[BreakdownResult]


class DailyResult(BaseModel):
    day: date
    calls: int
    cost_usd: float


def get_period(
    # « from » est un mot réservé de Python : le paramètre s'appelle `start` mais s'écrit
    # `?from=` dans l'URL (alias).
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> Period:
    """Lit `?from=AAAA-MM-JJ&to=AAAA-MM-JJ` ; les deux dates sont incluses (jours en UTC)."""
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="« from » doit précéder « to ».")
    return Period(
        start=datetime.combine(start, time.min, tzinfo=UTC) if start else None,
        # La fin du service est exclue : on prend minuit du lendemain pour inclure le dernier jour.
        end=datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC) if end else None,
    )


def get_cost_service(session: Annotated[Session, Depends(get_db_session)]) -> CostService:
    return CostService(session)


@router.get("/summary")
def summary(
    service: Annotated[CostService, Depends(get_cost_service)],
    period: Annotated[Period, Depends(get_period)],
) -> SummaryResult:
    return SummaryResult(
        totals=TotalsResult.model_validate(service.totals(period), from_attributes=True),
        by_model=[
            BreakdownResult.model_validate(row, from_attributes=True)
            for row in service.by_model(period)
        ],
        by_task=[
            BreakdownResult.model_validate(row, from_attributes=True)
            for row in service.by_task(period)
        ],
    )


@router.get("/daily")
def daily(
    service: Annotated[CostService, Depends(get_cost_service)],
    period: Annotated[Period, Depends(get_period)],
) -> list[DailyResult]:
    return [DailyResult.model_validate(row, from_attributes=True) for row in service.daily(period)]
