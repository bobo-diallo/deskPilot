from typing import Protocol

from app.domains.llm.schemas import LLMRequest, LLMResponse


class LLMProvider(Protocol):
    """Contrat commun à tous les fournisseurs (Anthropic, modèle local, faux pour les tests).

    Le reste de l'application ne connaît que ce contrat : changer de fournisseur
    ne demande donc aucune modification du code métier.
    """

    name: str

    def complete(self, request: LLMRequest) -> LLMResponse: ...
