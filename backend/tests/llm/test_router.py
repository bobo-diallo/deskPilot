import pytest

from app.domains.llm.pricing import PRICES
from app.domains.llm.router import Task, choose_model


def test_extraction_uses_the_stronger_model():
    assert choose_model(Task.EXTRACTION) == "claude-sonnet-5-5"


def test_simple_tasks_use_the_cheapest_model():
    assert choose_model(Task.SIMPLE) == "claude-haiku-5-5"


@pytest.mark.parametrize("task", list(Task))
def test_every_chosen_model_has_a_known_price(task):
    assert choose_model(task) in PRICES
