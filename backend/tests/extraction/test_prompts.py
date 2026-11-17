import pytest

from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.prompts import DEFAULT_PROMPT_VERSION, get_prompt
from app.domains.extraction.schemas import Invoice
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService
from app.evaluation.variants import VARIANTS


def test_the_default_version_is_v1():
    assert DEFAULT_PROMPT_VERSION == "v1"


def test_v2_keeps_the_v1_rules_and_adds_the_date_convention():
    v1, v2 = get_prompt("v1"), get_prompt("v2-date-convention")

    assert v1 in v2
    assert "mois/jour/année" in v2 and "jour/mois/année" in v2
    assert "mois/jour/année" not in v1


def test_an_unknown_version_is_refused():
    with pytest.raises(ValueError, match="v99"):
        get_prompt("v99")


def test_the_extractor_sends_the_prompt_of_the_requested_version(session):
    provider = FakeProvider(parsed=Invoice())
    extractor = ClaudeExtractor(LLMService(provider, session), prompt_version="v2-date-convention")

    extractor.extract(b"%PDF-1", "application/pdf")

    assert provider.received[0].system == get_prompt("v2-date-convention")


def test_the_extractor_uses_v1_by_default(session):
    provider = FakeProvider(parsed=Invoice())

    ClaudeExtractor(LLMService(provider, session)).extract(b"%PDF-1", "application/pdf")

    assert provider.received[0].system == get_prompt("v1")


@pytest.mark.parametrize("name", list(VARIANTS))
def test_every_evaluation_variant_can_be_built(session, name):
    extractor = VARIANTS[name].build(LLMService(FakeProvider(), session))

    assert callable(extractor.extract)
