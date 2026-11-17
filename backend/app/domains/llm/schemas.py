from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "user" ou "assistant"
    content: str


@dataclass(frozen=True)
class LLMAttachment:
    """Fichier joint à la demande (PDF ou image) que le modèle doit lire."""

    media_type: str
    data: bytes


@dataclass(frozen=True)
class LLMRequest:
    """Ce qu'on demande à un modèle, indépendamment du fournisseur."""

    model: str
    messages: list[LLMMessage]
    system: str | None = None
    max_tokens: int = 1024
    # Fichiers joints au dernier message de l'utilisateur.
    attachments: list[LLMAttachment] = field(default_factory=list)
    # Si fourni, la réponse est contrainte à ce schéma Pydantic (sortie structurée).
    response_schema: type[BaseModel] | None = None


@dataclass(frozen=True)
class LLMResponse:
    """Ce qu'un modèle répond, avec ce qu'il faut pour calculer le coût."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    # Objet validé quand une `response_schema` était demandée, sinon None.
    parsed: BaseModel | None = None
