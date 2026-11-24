from app.config import Settings
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.providers.factory import build_llm_provider
from app.domains.llm.providers.retrying import RetryingProvider


def test_the_real_provider_is_wrapped_with_retries():
    provider = build_llm_provider(Settings(anthropic_api_key="cle-de-test", _env_file=None))

    assert isinstance(provider, RetryingProvider)


def test_the_sdk_does_not_retry_on_its_own():
    # Deux couches de nouvelles tentatives se multiplieraient (3 x 3 essais) : seule la nôtre agit.
    provider = build_llm_provider(Settings(anthropic_api_key="cle-de-test", _env_file=None))

    sdk_client = provider._provider._client
    assert isinstance(provider._provider, AnthropicProvider)
    assert sdk_client.max_retries == 0


def test_the_timeout_comes_from_the_settings():
    settings = Settings(anthropic_api_key="cle-de-test", llm_timeout_seconds=12.0, _env_file=None)

    sdk_client = build_llm_provider(settings)._provider._client

    assert sdk_client.timeout == 12.0


def test_the_number_of_retries_comes_from_the_settings():
    settings = Settings(anthropic_api_key="cle-de-test", llm_max_retries=5, _env_file=None)

    assert build_llm_provider(settings)._max_retries == 5
