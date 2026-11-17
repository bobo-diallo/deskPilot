import pytest

from app.domains.llm.pricing import UnknownModelError, compute_cost_usd


def test_cost_of_one_million_tokens_each_way_for_sonnet():
    cost = compute_cost_usd("claude-sonnet-5-5", input_tokens=1_000_000, output_tokens=1_000_000)

    # 2 $ par million de tokens en entrée + 10 $ en sortie
    assert cost == pytest.approx(12.0)


def test_cost_of_a_small_haiku_call():
    cost = compute_cost_usd("claude-haiku-5-5", input_tokens=1_000, output_tokens=500)

    assert cost == pytest.approx(0.00035)


def test_unknown_model_raises_a_clear_error():
    with pytest.raises(UnknownModelError, match="claude-inconnu"):
        compute_cost_usd("claude-inconnu", input_tokens=1, output_tokens=1)
