from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.schemas import Invoice
from app.domains.llm.router import Task, choose_model
from app.domains.llm.schemas import LLMAttachment, LLMMessage, LLMRequest
from app.domains.llm.service import LLMService

SYSTEM_PROMPT = (
    "Tu extrais les champs d'une facture à partir du document fourni. "
    "Si une information est absente ou illisible, laisse le champ vide : "
    "n'invente jamais de valeur. "
    "Les montants sont des nombres décimaux sans symbole monétaire ni séparateur de milliers."
)


class ClaudeExtractor:
    """Extracteur qui demande à Claude de lire le document (PDF ou image) directement."""

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput:
        request = LLMRequest(
            model=choose_model(Task.EXTRACTION),
            system=SYSTEM_PROMPT,
            messages=[LLMMessage(role="user", content="Extrais les champs de cette facture.")],
            attachments=[LLMAttachment(media_type=media_type, data=content)],
            response_schema=Invoice,
            max_tokens=8192,
        )
        response = self._llm_service.complete(request)

        if not isinstance(response.parsed, Invoice):
            raise ExtractionError("Le modèle n'a pas renvoyé de facture structurée")
        return ExtractionOutput(data=response.parsed, model=response.model)
