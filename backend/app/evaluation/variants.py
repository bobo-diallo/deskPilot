from collections.abc import Callable
from dataclasses import dataclass

from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.extractors.text_layer import TextLayerExtractor
from app.domains.extraction.ports import DocumentExtractor
from app.domains.llm.service import LLMService


@dataclass(frozen=True)
class VariantSpec:
    """Une façon d'extraire à comparer, avec une estimation de tokens pour prévoir le coût."""

    description: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    build: Callable[[LLMService], DocumentExtractor]


# Les variantes « v1 » épinglent leur version de prompt : le défaut de production a changé,
# mais les anciennes mesures doivent rester reproductibles.
# Estimations mesurées en story 02 : une facture PDF d'une page = ~3 200 tokens en entrée.
VARIANTS: dict[str, VariantSpec] = {
    "sonnet-vision": VariantSpec(
        description="Claude Sonnet 5.5 lit le PDF ou l'image",
        model="claude-sonnet-5-5",
        estimated_input_tokens=3_200,
        estimated_output_tokens=250,
        build=lambda llm: ClaudeExtractor(llm, model="claude-sonnet-5-5", prompt_version="v1"),
    ),
    "haiku-vision": VariantSpec(
        description="Claude Haiku 5.5 lit le PDF ou l'image",
        model="claude-haiku-5-5",
        estimated_input_tokens=3_200,
        estimated_output_tokens=250,
        build=lambda llm: ClaudeExtractor(llm, model="claude-haiku-5-5", prompt_version="v1"),
    ),
    # Prompt v2 : même modèle, même jeu, seule la consigne sur les dates change.
    "haiku-vision-v2": VariantSpec(
        description="Claude Haiku 5.5 lit le PDF ou l'image, prompt v2 (convention des dates)",
        model="claude-haiku-5-5",
        estimated_input_tokens=3_200,
        estimated_output_tokens=250,
        build=lambda llm: ClaudeExtractor(
            llm, model="claude-haiku-5-5", prompt_version="v2-date-convention"
        ),
    ),
    # Texte intégré du PDF seulement (sans image) : bien moins de tokens, PDF numériques seuls.
    "sonnet-text": VariantSpec(
        description="Texte extrait du PDF (pypdf), lu par Claude Sonnet 5.5",
        model="claude-sonnet-5-5",
        estimated_input_tokens=700,
        estimated_output_tokens=250,
        build=lambda llm: TextLayerExtractor(llm, model="claude-sonnet-5-5", prompt_version="v1"),
    ),
    "haiku-text": VariantSpec(
        description="Texte extrait du PDF (pypdf), lu par Claude Haiku 5.5",
        model="claude-haiku-5-5",
        estimated_input_tokens=700,
        estimated_output_tokens=250,
        build=lambda llm: TextLayerExtractor(llm, model="claude-haiku-5-5", prompt_version="v1"),
    ),
}
