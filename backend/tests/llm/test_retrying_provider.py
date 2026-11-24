import pytest

from app.domains.llm.errors import (
    LLMAuthenticationError,
    LLMRateLimitedError,
    LLMRefusedError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.domains.llm.providers.retrying import RetryingProvider
from app.domains.llm.schemas import LLMMessage, LLMRequest, LLMResponse

REQUEST = LLMRequest(model="claude-haiku-5-5", messages=[LLMMessage("user", "Salut")])
OK = LLMResponse(text="ok", model="claude-haiku-5-5", input_tokens=1, output_tokens=1)


class FlakyProvider:
    """Échoue avec les erreurs données, dans l'ordre, puis répond normalement."""

    name = "flaky"

    def __init__(self, *errors: Exception):
        self._errors = list(errors)
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        if self._errors:
            raise self._errors.pop(0)
        return OK


def make(provider, *, max_retries=3, sleeps=None, jitter=lambda: 1.0, **kwargs):
    sleeps = sleeps if sleeps is not None else []
    return RetryingProvider(
        provider,
        max_retries=max_retries,
        base_delay=1.0,
        max_delay=10.0,
        sleep=sleeps.append,
        jitter=jitter,
        **kwargs,
    )


def test_a_successful_call_is_not_retried_and_does_not_wait():
    sleeps: list[float] = []
    provider = FlakyProvider()

    response = make(provider, sleeps=sleeps).complete(REQUEST)

    assert response is OK
    assert provider.calls == 1
    assert sleeps == []


def test_a_temporary_error_is_retried_until_it_works():
    provider = FlakyProvider(LLMUnavailableError("panne"), LLMTimeoutError("lent"))

    response = make(provider).complete(REQUEST)

    assert response is OK
    assert provider.calls == 3


def test_it_gives_up_after_the_maximum_number_of_retries():
    provider = FlakyProvider(*[LLMUnavailableError("panne")] * 10)

    with pytest.raises(LLMUnavailableError):
        make(provider, max_retries=2).complete(REQUEST)

    assert provider.calls == 3  # 1 appel puis 2 nouvelles tentatives


def test_the_delay_doubles_at_each_retry():
    sleeps: list[float] = []
    provider = FlakyProvider(*[LLMUnavailableError("panne")] * 3)

    make(provider, sleeps=sleeps, max_retries=3).complete(REQUEST)

    assert sleeps == [1.0, 2.0, 4.0]


def test_the_delay_is_capped():
    sleeps: list[float] = []
    provider = FlakyProvider(*[LLMUnavailableError("panne")] * 5)

    make(provider, sleeps=sleeps, max_retries=5).complete(REQUEST)

    assert sleeps == [1.0, 2.0, 4.0, 8.0, 10.0]


def test_jitter_shortens_the_delay_so_clients_do_not_retry_together():
    sleeps: list[float] = []
    provider = FlakyProvider(LLMUnavailableError("panne"))

    make(provider, sleeps=sleeps, jitter=lambda: 0.0).complete(REQUEST)

    assert sleeps == [0.5]  # la moitié du délai quand le hasard vaut 0


def test_the_retry_after_of_the_provider_is_obeyed():
    sleeps: list[float] = []
    provider = FlakyProvider(LLMRateLimitedError("trop vite", retry_after=3.0))

    make(provider, sleeps=sleeps).complete(REQUEST)

    assert sleeps == [3.0]


def test_it_does_not_wait_longer_than_the_maximum_delay():
    sleeps: list[float] = []
    provider = FlakyProvider(LLMRateLimitedError("trop vite", retry_after=120.0))

    with pytest.raises(LLMRateLimitedError):
        make(provider, sleeps=sleeps).complete(REQUEST)

    assert sleeps == []
    assert provider.calls == 1


@pytest.mark.parametrize("error", [LLMAuthenticationError("clé"), LLMRefusedError("refus")])
def test_a_permanent_error_is_raised_at_once(error):
    provider = FlakyProvider(error)

    with pytest.raises(type(error)):
        make(provider).complete(REQUEST)

    assert provider.calls == 1


def test_zero_retries_means_a_single_attempt():
    provider = FlakyProvider(LLMUnavailableError("panne"))

    with pytest.raises(LLMUnavailableError):
        make(provider, max_retries=0).complete(REQUEST)

    assert provider.calls == 1


def test_it_keeps_the_name_of_the_wrapped_provider():
    assert make(FlakyProvider()).name == "flaky"
