from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass(frozen=True)
class ToolSpec:
    """Un outil que le modèle peut demander à utiliser : nom, rôle et forme des arguments."""

    name: str
    description: str  # c'est ce texte qui permet au modèle de choisir le bon outil
    input_schema: dict  # schéma JSON des arguments


@dataclass(frozen=True)
class ToolCall:
    """Le modèle demande d'exécuter un outil avec ces arguments (il ne l'exécute pas lui-même)."""

    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "user" ou "assistant"
    # Un texte, ou une liste de blocs bruts (tour d'assistant avec appels d'outils, résultats
    # d'outils) transmis tels quels au fournisseur.
    content: str | list[dict]


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
    # Outils proposés au modèle (agent). Vide : réponse simple.
    tools: list[ToolSpec] = field(default_factory=list)


@dataclass(frozen=True)
class LLMResponse:
    """Ce qu'un modèle répond, avec ce qu'il faut pour calculer le coût."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    # Objet validé quand une `response_schema` était demandée, sinon None.
    parsed: BaseModel | None = None
    # Appels d'outils demandés par le modèle (liste vide pour une réponse simple).
    tool_calls: list[ToolCall] = field(default_factory=list)
    # Blocs bruts de la réponse, à rejouer tels quels dans le tour d'assistant suivant.
    content_blocks: list[dict] = field(default_factory=list)
    stop_reason: str | None = None  # "end_turn", "tool_use"…
