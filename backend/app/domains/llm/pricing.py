from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    """Tarif d'un modèle, en dollars par million de tokens."""

    input_per_million: float
    output_per_million: float


# Tarifs de l'API Anthropic (novembre 2026). À mettre à jour si les prix changent.
# Simplification volontaire : pas de tarif spécial pour les très longs prompts ni pour le cache.
PRICES: dict[str, ModelPrice] = {
    "claude-sonnet-5-5": ModelPrice(input_per_million=2.00, output_per_million=10.00),
    "claude-haiku-5-5": ModelPrice(input_per_million=0.10, output_per_million=0.50),
    "claude-opus-5-5": ModelPrice(input_per_million=4.00, output_per_million=20.00),
}


class UnknownModelError(Exception):
    """Le modèle n'a pas de tarif connu : mieux vaut échouer que facturer à 0."""


def compute_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = PRICES.get(model)
    if price is None:
        raise UnknownModelError(f"Aucun tarif connu pour le modèle {model}")
    return (
        input_tokens * price.input_per_million + output_tokens * price.output_per_million
    ) / 1_000_000
