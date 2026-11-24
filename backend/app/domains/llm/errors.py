class LLMRefusedError(Exception):
    """Le modèle a refusé de répondre (filtre de sécurité). La requête n'a pas de réponse utile."""


class LLMInvalidOutputError(Exception):
    """La réponse du modèle ne respecte pas le schéma demandé (ex. valeur non numérique)."""


class LLMProviderError(Exception):
    """Le fournisseur n'a pas pu répondre. Le reste de l'application ne connaît que ces erreurs,
    jamais celles du SDK : changer de fournisseur ne change donc pas la gestion des pannes.

    `retryable` dit si une nouvelle tentative a un sens (panne passagère) ou non (requête ou clé
    invalide : réessayer ne la réparera pas et coûterait de l'argent).
    """

    retryable = False

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        # Délai demandé par le fournisseur (en-tête `retry-after`), en secondes, s'il en a donné un.
        self.retry_after = retry_after


class LLMRateLimitedError(LLMProviderError):
    """Trop de requêtes (HTTP 429) : il faut ralentir."""

    retryable = True


class LLMUnavailableError(LLMProviderError):
    """Panne ou surcharge du fournisseur (HTTP 5xx, connexion impossible)."""

    retryable = True


class LLMTimeoutError(LLMProviderError):
    """Le fournisseur n'a pas répondu dans le délai prévu."""

    retryable = True


class LLMAuthenticationError(LLMProviderError):
    """Clé absente, invalide ou sans droit (HTTP 401 ou 403)."""


class LLMRequestRejectedError(LLMProviderError):
    """Le fournisseur refuse la requête telle quelle (HTTP 400, 404…) : bogue de notre côté."""
