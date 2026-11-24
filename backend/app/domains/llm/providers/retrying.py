import logging
import random
import time
from collections.abc import Callable

from app.domains.llm.errors import LLMProviderError
from app.domains.llm.ports import LLMProvider
from app.domains.llm.schemas import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class RetryingProvider:
    """Enrobe un fournisseur : retente les pannes passagères avec un délai qui double.

    Il respecte le même contrat `LLMProvider` que le fournisseur enrobé : le code appelant ne
    sait pas qu'il existe (même idée qu'un middleware ou qu'un décorateur).
    """

    def __init__(
        self,
        provider: LLMProvider,
        *,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 20.0,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
    ):
        self._provider = provider
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        # `sleep` et `jitter` sont injectés : les tests passent des faux et ne dorment pas.
        self._sleep = sleep
        self._jitter = jitter
        self.name = provider.name

    def complete(self, request: LLMRequest) -> LLMResponse:
        attempt = 0
        while True:
            try:
                return self._provider.complete(request)
            except LLMProviderError as error:
                if not error.retryable or attempt >= self._max_retries:
                    raise
                delay = self._delay(error, attempt)
                if delay is None:
                    raise  # le fournisseur demande une attente plus longue que notre maximum
                attempt += 1
                logger.warning(
                    "Appel au modèle échoué (%s), nouvelle tentative %d/%d dans %.1f s",
                    type(error).__name__,
                    attempt,
                    self._max_retries,
                    delay,
                )
                self._sleep(delay)

    def _delay(self, error: LLMProviderError, attempt: int) -> float | None:
        """Secondes à attendre avant la prochaine tentative, ou None si c'est trop long."""
        if error.retry_after is not None:
            return error.retry_after if error.retry_after <= self._max_delay else None
        delay = min(self._base_delay * 2**attempt, self._max_delay)
        # Le hasard raccourcit le délai de 0 à 50 % : des clients qui échouent ensemble ne
        # retentent pas tous à la même seconde (sinon ils rechargent le serveur en rafale).
        return delay * (0.5 + 0.5 * self._jitter())
