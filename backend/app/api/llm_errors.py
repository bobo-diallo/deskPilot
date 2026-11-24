import math

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domains.llm.errors import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitedError,
    LLMTimeoutError,
    LLMUnavailableError,
)

# Pour chaque panne du fournisseur : code HTTP et message affichable (jamais le détail technique).
_RESPONSES: list[tuple[type[LLMProviderError], int, str]] = [
    (LLMRateLimitedError, 503, "Le service d'IA est très sollicité. Réessayez dans un instant."),
    (
        LLMUnavailableError,
        502,
        "Le modèle d'IA est momentanément indisponible. Réessayez plus tard.",
    ),
    (LLMTimeoutError, 504, "Le modèle d'IA a mis trop de temps à répondre."),
    (
        LLMAuthenticationError,
        503,
        "L'accès au modèle d'IA est refusé : vérifiez la clé ANTHROPIC_API_KEY.",
    ),
]
_DEFAULT = (502, "Le modèle d'IA a rejeté la requête.")


async def handle_provider_error(request: Request, error: LLMProviderError) -> JSONResponse:
    status, message = next(
        ((code, text) for kind, code, text in _RESPONSES if isinstance(error, kind)), _DEFAULT
    )
    headers = {}
    if error.retry_after is not None:
        headers["Retry-After"] = str(math.ceil(error.retry_after))
    return JSONResponse({"detail": message}, status_code=status, headers=headers)


def register(app: FastAPI) -> None:
    """Une seule correspondance erreur → réponse HTTP pour toutes les routes qui appellent un LLM"""
    app.add_exception_handler(LLMProviderError, handle_provider_error)
