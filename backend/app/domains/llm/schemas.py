from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "user" ou "assistant"
    content: str


@dataclass(frozen=True)
class LLMRequest:
    """Ce qu'on demande à un modèle, indépendamment du fournisseur."""

    model: str
    messages: list[LLMMessage]
    system: str | None = None
    max_tokens: int = 1024


@dataclass(frozen=True)
class LLMResponse:
    """Ce qu'un modèle répond, avec ce qu'il faut pour calculer le coût."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
