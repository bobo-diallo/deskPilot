from collections.abc import Callable
from dataclasses import dataclass

from app.domains.extraction.extractors.audio import AudioExtractor
from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.extractors.text_layer import TextLayerExtractor
from app.domains.extraction.ports import DocumentExtractor
from app.domains.llm.service import LLMService
from app.domains.transcription.transcribers.faster_whisper import FasterWhisperTranscriber


@dataclass(frozen=True)
class VariantSpec:
    """Une façon d'extraire à comparer, avec une estimation de tokens pour prévoir le coût."""

    description: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    prompt_version: str  # doit être celle que `build` utilise (un test le vérifie)
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
        prompt_version="v1",
        build=lambda llm: ClaudeExtractor(llm, model="claude-sonnet-5-5", prompt_version="v1"),
    ),
    "haiku-vision": VariantSpec(
        description="Claude Haiku 5.5 lit le PDF ou l'image",
        model="claude-haiku-5-5",
        estimated_input_tokens=3_200,
        estimated_output_tokens=250,
        prompt_version="v1",
        build=lambda llm: ClaudeExtractor(llm, model="claude-haiku-5-5", prompt_version="v1"),
    ),
    # Prompt v2 : même modèle, même jeu, seule la consigne sur les dates change.
    "haiku-vision-v2": VariantSpec(
        description="Claude Haiku 5.5 lit le PDF ou l'image, prompt v2 (convention des dates)",
        model="claude-haiku-5-5",
        estimated_input_tokens=3_200,
        estimated_output_tokens=250,
        prompt_version="v2-date-convention",
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
        prompt_version="v1",
        build=lambda llm: TextLayerExtractor(llm, model="claude-sonnet-5-5", prompt_version="v1"),
    ),
    "haiku-text": VariantSpec(
        description="Texte extrait du PDF (pypdf), lu par Claude Haiku 5.5",
        model="claude-haiku-5-5",
        estimated_input_tokens=700,
        estimated_output_tokens=250,
        prompt_version="v1",
        build=lambda llm: TextLayerExtractor(llm, model="claude-haiku-5-5", prompt_version="v1"),
    ),
}


# Épinglée comme les autres : la mesure audio doit rester reproductible si le défaut change.
_AUDIO_PROMPT_VERSION = "v2-date-convention"


def _whisper_variant(size: str) -> VariantSpec:
    # Transcription locale (gratuite) puis Claude Haiku sur le texte : seul le texte coûte.
    return VariantSpec(
        description=f"Whisper {size} (local) transcrit la dictée, Claude Haiku 5.5 la structure",
        model="claude-haiku-5-5",
        # Calibré sur la première mesure audio : 0,0006 $ par dictée, réflexion comprise.
        estimated_input_tokens=1_200,
        estimated_output_tokens=900,
        prompt_version=_AUDIO_PROMPT_VERSION,
        build=lambda llm: AudioExtractor(
            FasterWhisperTranscriber(size),
            llm,
            model="claude-haiku-5-5",
            prompt_version=_AUDIO_PROMPT_VERSION,
        ),
    )


VARIANTS.update(
    {f"whisper-{size}-haiku": _whisper_variant(size) for size in ("tiny", "base", "small")}
)
