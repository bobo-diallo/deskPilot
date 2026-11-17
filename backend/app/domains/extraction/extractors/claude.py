from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.prompts import DEFAULT_PROMPT_VERSION, get_prompt
from app.domains.extraction.schemas import Invoice
from app.domains.llm.router import Task, choose_model
from app.domains.llm.schemas import LLMAttachment, LLMMessage, LLMRequest
from app.domains.llm.service import LLMService


class ClaudeExtractor:
    """Extracteur qui demande à Claude de lire le document (PDF ou image) directement."""

    def __init__(
        self,
        llm_service: LLMService,
        model: str | None = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ):
        self._llm_service = llm_service
        self._system_prompt = get_prompt(prompt_version)
        # Modèle imposé (utile pour comparer) ; sinon le routeur choisit selon la tâche.
        self._model = model

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput:
        request = LLMRequest(
            model=self._model or choose_model(Task.EXTRACTION),
            system=self._system_prompt,
            messages=[LLMMessage(role="user", content="Extrais les champs de cette facture.")],
            attachments=[LLMAttachment(media_type=media_type, data=content)],
            response_schema=Invoice,
            max_tokens=8192,
        )
        response = self._llm_service.complete(request)

        if not isinstance(response.parsed, Invoice):
            raise ExtractionError("Le modèle n'a pas renvoyé de facture structurée")
        return ExtractionOutput(data=response.parsed, model=response.model)
