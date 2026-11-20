from datetime import UTC, datetime

import pytest

from app.domains.costs.service import CostService, Period
from app.domains.llm.models import ApiCall


def add_call(
    session,
    *,
    model="claude-haiku-5-5",
    task: str | None = "extraction",
    cost=0.01,
    latency=100,
    day=(2026, 11, 10),
    input_tokens=1_000,
    output_tokens=200,
):
    session.add(
        ApiCall(
            provider="anthropic",
            model=model,
            task=task,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency,
            created_at=datetime(*day, 12, 0, tzinfo=UTC),
        )
    )
    session.commit()


def test_totals_of_an_empty_journal_are_zero(session):
    totals = CostService(session).totals()

    assert (totals.calls, totals.input_tokens, totals.output_tokens) == (0, 0, 0)
    assert totals.cost_usd == 0.0


def test_totals_add_up_every_call(session):
    add_call(session, cost=0.01, input_tokens=1_000, output_tokens=200)
    add_call(session, cost=0.02, input_tokens=3_000, output_tokens=400)

    totals = CostService(session).totals()

    assert totals.calls == 2
    assert (totals.input_tokens, totals.output_tokens) == (4_000, 600)
    assert totals.cost_usd == pytest.approx(0.03)


def test_totals_only_count_the_requested_period(session):
    add_call(session, cost=1.0, day=(2026, 11, 9))
    add_call(session, cost=2.0, day=(2026, 11, 10))
    add_call(session, cost=4.0, day=(2026, 11, 11))
    period = Period(
        start=datetime(2026, 11, 10, tzinfo=UTC), end=datetime(2026, 11, 11, tzinfo=UTC)
    )

    totals = CostService(session).totals(period)

    # Le début est inclus, la fin est exclue : seul le 10 novembre compte.
    assert totals.calls == 1
    assert totals.cost_usd == pytest.approx(2.0)


def test_by_model_groups_calls_and_sorts_by_decreasing_cost(session):
    add_call(session, model="claude-haiku-5-5", cost=0.01)
    add_call(session, model="claude-haiku-5-5", cost=0.01)
    add_call(session, model="claude-sonnet-5-5", cost=0.5)

    rows = CostService(session).by_model()

    assert [row.key for row in rows] == ["claude-sonnet-5-5", "claude-haiku-5-5"]
    assert [row.calls for row in rows] == [1, 2]
    assert rows[1].cost_usd == pytest.approx(0.02)


def test_by_task_keeps_calls_without_task_in_their_own_group(session):
    add_call(session, task="agent", cost=0.2)
    add_call(session, task=None, cost=0.1)

    rows = CostService(session).by_task()

    assert {row.key: row.calls for row in rows} == {"agent": 1, None: 1}


def test_latency_percentiles_use_the_nearest_rank_method(session):
    for latency in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1_000]:
        add_call(session, latency=latency)

    row = CostService(session).by_model()[0]

    assert row.latency_p50_ms == 500
    assert row.latency_p95_ms == 1_000


def test_daily_costs_are_grouped_by_day_in_chronological_order(session):
    add_call(session, cost=0.1, day=(2026, 11, 12))
    add_call(session, cost=0.2, day=(2026, 11, 10))
    add_call(session, cost=0.3, day=(2026, 11, 10))

    days = CostService(session).daily()

    assert [(d.day.isoformat(), d.calls) for d in days] == [("2026-11-10", 2), ("2026-11-12", 1)]
    assert days[0].cost_usd == pytest.approx(0.5)
