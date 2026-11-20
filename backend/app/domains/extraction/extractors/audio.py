from app.domains.documents.file_types import is_audio
from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.prompts import DEFAULT_PROMPT_VERSION, get_prompt
from app.domains.extraction.schemas import Invoice
from app.domains.llm.router import Task, choose_model
from app.domains.llm.schemas import LLMMessage, LLMRequest
from app.domains.llm.service import LLMService
from app.domains.transcription.errors import TranscriptionError
from app.domains.transcription.ports import Transcriber

# La transcription automatique se trompe sur les noms propres et peut écrire les nombres en
# lettres : on prévient le modèle plutôt que de lui laisser prendre le texte pour exact.
_DICTATION_INSTRUCTION = (
    "Voici la transcription automatique d'une facture dictée à voix haute. "
    "Elle peut contenir des erreurs d'orthographe, surtout sur les noms propres. "
    "Les nombres peuvent être écrits en lettres : convertis-les en chiffres. "
    "Extrais les champs de cette facture."
)


class AudioExtractor:
    """Extracteur pour une facture dictée : transcrit en local, puis structure le texte.

    L'audio ne quitte jamais la machine : seul le texte transcrit est envoyé au modèle.
    """

    def __init__(
        self,
        transcriber: Transcriber,
        llm_service: LLMService,
        model: str | None = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
        language: str = "fr",
    ):
        self._transcriber = transcriber
        self._llm_service = llm_service
        self._model = model
        self._system_prompt = get_prompt(prompt_version)
        self._language = language

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput:
        if not is_audio(media_type):
            raise ExtractionError("Cet extracteur ne traite que les fichiers audio")

        try:
            transcript = self._transcriber.transcribe(content, language=self._language)
        except TranscriptionError as error:
            raise ExtractionError(f"Transcription impossible : {error}") from error
        if not transcript.text.strip():
            raise ExtractionError("Aucune parole détectée dans l'enregistrement")

        request = LLMRequest(
            model=self._model or choose_model(Task.EXTRACTION),
            task=Task.EXTRACTION,
            system=self._system_prompt,
            messages=[
                LLMMessage(
                    role="user",
                    content=f"{_DICTATION_INSTRUCTION}\n\nTranscription :\n{transcript.text}",
                )
            ],
            response_schema=Invoice,
            max_tokens=8192,
        )
        response = self._llm_service.complete(request)

        if not isinstance(response.parsed, Invoice):
            raise ExtractionError("Le modèle n'a pas renvoyé de facture structurée")
        return ExtractionOutput(data=response.parsed, model=response.model, transcript=transcript)
