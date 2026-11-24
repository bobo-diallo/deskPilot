import anthropic

from app.config import Settings
from app.domains.llm.ports import LLMProvider
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.providers.retrying import RetryingProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Fournisseur réel prêt à l'emploi : Anthropic, avec délai maximum et nouvelles tentatives.

    Le SDK retente par défaut 2 fois en silence ; on le coupe (`max_retries=0`) pour que seule
    notre couche `RetryingProvider` retente : on sait alors combien d'essais ont lieu, on les
    journalise, et on les teste.
    """
    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        max_retries=0,
        timeout=settings.llm_timeout_seconds,
    )
    return RetryingProvider(AnthropicProvider(client), max_retries=settings.llm_max_retries)
