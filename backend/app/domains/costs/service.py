import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domains.llm.models import ApiCall


@dataclass(frozen=True)
class Period:
    """Fenêtre de temps : le début est inclus, la fin est exclue. Un côté vide = pas de borne."""

    start: datetime | None = None
    end: datetime | None = None


@dataclass(frozen=True)
class CostTotals:
    calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass(frozen=True)
class CostBreakdown:
    """Une ligne de ventilation (un modèle, ou une tâche) avec coût et latence."""

    key: str | None  # None : appels sans tâche enregistrée (antérieurs à la story 06a)
    calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_p50_ms: int
    latency_p95_ms: int


@dataclass(frozen=True)
class DailyCost:
    day: date
    calls: int
    cost_usd: float


def percentile(values: list[int], rank: float) -> int:
    """Percentile « rang le plus proche » : la plus petite valeur couvrant `rank` % des mesures.

    SQLite n'a pas de fonction percentile : on le calcule ici, sur la liste des latences.
    """
    if not values:
        return 0
    ordered = sorted(values)
    index = math.ceil(rank / 100 * len(ordered)) - 1
    return ordered[max(index, 0)]


class CostService:
    """Lit le journal `api_calls` et en tire des totaux, des ventilations et une série par jour."""

    def __init__(self, session: Session):
        self._session = session

    def totals(self, period: Period = Period()) -> CostTotals:
        query = self._within(
            select(
                func.count(ApiCall.id),
                func.coalesce(func.sum(ApiCall.input_tokens), 0),
                func.coalesce(func.sum(ApiCall.output_tokens), 0),
                func.coalesce(func.sum(ApiCall.cost_usd), 0.0),
            ),
            period,
        )
        calls, input_tokens, output_tokens, cost = self._session.execute(query).one()
        return CostTotals(calls, input_tokens, output_tokens, float(cost))

    def by_model(self, period: Period = Period()) -> list[CostBreakdown]:
        return self._breakdown(ApiCall.model, period)

    def by_task(self, period: Period = Period()) -> list[CostBreakdown]:
        return self._breakdown(ApiCall.task, period)

    def daily(self, period: Period = Period()) -> list[DailyCost]:
        day = func.date(ApiCall.created_at)
        query = self._within(
            select(day, func.count(ApiCall.id), func.sum(ApiCall.cost_usd)), period
        )
        rows = self._session.execute(query.group_by(day).order_by(day)).all()
        return [DailyCost(date.fromisoformat(d), calls, float(cost)) for d, calls, cost in rows]

    def _breakdown(self, column, period: Period) -> list[CostBreakdown]:
        query = self._within(
            select(
                column,
                func.count(ApiCall.id),
                func.sum(ApiCall.input_tokens),
                func.sum(ApiCall.output_tokens),
                func.sum(ApiCall.cost_usd),
            ),
            period,
        )
        rows = self._session.execute(query.group_by(column)).all()

        # Les latences se lisent à part : un percentile ne s'agrège pas en SQL.
        latencies: dict[str | None, list[int]] = defaultdict(list)
        for key, latency in self._session.execute(
            self._within(select(column, ApiCall.latency_ms), period)
        ):
            latencies[key].append(latency)

        breakdown = [
            CostBreakdown(
                key=key,
                calls=calls,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=float(cost),
                latency_p50_ms=percentile(latencies[key], 50),
                latency_p95_ms=percentile(latencies[key], 95),
            )
            for key, calls, input_tokens, output_tokens, cost in rows
        ]
        return sorted(breakdown, key=lambda row: row.cost_usd, reverse=True)

    @staticmethod
    def _within(query: Select, period: Period) -> Select:
        if period.start is not None:
            query = query.where(ApiCall.created_at >= period.start)
        if period.end is not None:
            query = query.where(ApiCall.created_at < period.end)
        return query
