from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.domains.llm.errors import (
    LLMAuthenticationError,
    LLMRateLimitedError,
    LLMRequestRejectedError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.schemas import LLMMessage, LLMRequest

REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(error_class, status: int, headers: dict | None = None):
    response = httpx.Response(status, request=REQUEST, headers=headers or {})
    return error_class("erreur", response=response, body=None)


class FailingMessages:
    def __init__(self, error):
        self.error = error

    def create(self, **kwargs):
        raise self.error

    parse = create


def call_with(error):
    provider = AnthropicProvider(SimpleNamespace(messages=FailingMessages(error)))
    request = LLMRequest(model="claude-haiku-5-5", messages=[LLMMessage("user", "Salut")])
    return provider.complete(request)


@pytest.mark.parametrize(
    ("sdk_error", "expected"),
    [
        (status_error(anthropic.RateLimitError, 429), LLMRateLimitedError),
        (status_error(anthropic.InternalServerError, 500), LLMUnavailableError),
        (status_error(anthropic.InternalServerError, 529), LLMUnavailableError),
        (anthropic.APITimeoutError(request=REQUEST), LLMTimeoutError),
        (anthropic.APIConnectionError(request=REQUEST), LLMUnavailableError),
        (status_error(anthropic.AuthenticationError, 401), LLMAuthenticationError),
        (status_error(anthropic.PermissionDeniedError, 403), LLMAuthenticationError),
        (status_error(anthropic.BadRequestError, 400), LLMRequestRejectedError),
        (status_error(anthropic.NotFoundError, 404), LLMRequestRejectedError),
    ],
)
def test_sdk_errors_become_our_own_errors(sdk_error, expected):
    with pytest.raises(expected):
        call_with(sdk_error)


def test_the_original_sdk_error_stays_attached_for_debugging():
    sdk_error = status_error(anthropic.RateLimitError, 429)

    with pytest.raises(LLMRateLimitedError) as caught:
        call_with(sdk_error)

    assert caught.value.__cause__ is sdk_error


def test_the_retry_after_header_is_kept_as_a_number_of_seconds():
    with pytest.raises(LLMRateLimitedError) as caught:
        call_with(status_error(anthropic.RateLimitError, 429, {"retry-after": "7"}))

    assert caught.value.retry_after == 7.0


def test_an_unreadable_retry_after_header_is_ignored():
    with pytest.raises(LLMRateLimitedError) as caught:
        call_with(status_error(anthropic.RateLimitError, 429, {"retry-after": "demain"}))

    assert caught.value.retry_after is None


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (LLMRateLimitedError("x"), True),
        (LLMUnavailableError("x"), True),
        (LLMTimeoutError("x"), True),
        (LLMAuthenticationError("x"), False),
        (LLMRequestRejectedError("x"), False),
    ],
)
def test_only_temporary_errors_are_retryable(error, retryable):
    assert error.retryable is retryable
