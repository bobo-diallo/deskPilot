import io

from pypdf import PdfReader

from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.extractors.claude import SYSTEM_PROMPT
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.schemas import Invoice
from app.domains.llm.router import Task, choose_model
from app.domains.llm.schemas import LLMMessage, LLMRequest
from app.domains.llm.service import LLMService


def _pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class TextLayerExtractor:
    """Extracteur « texte seul » : lit le texte intégré au PDF, sans envoyer d'images de page.

    Beaucoup moins de tokens qu'envoyer le PDF, mais ne fonctionne que pour les PDF numériques :
    un scan n'a pas de couche de texte (il faudrait alors un OCR ou la vision).
    """

    def __init__(self, llm_service: LLMService, model: str | None = None):
        self._llm_service = llm_service
        self._model = model

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput:
        if media_type != "application/pdf":
            raise ExtractionError("Seuls les PDF avec une couche de texte sont pris en charge")

        text = _pdf_text(content)
        if not text.strip():
            raise ExtractionError("Aucune couche de texte dans ce PDF (probablement un scan)")

        request = LLMRequest(
            model=self._model or choose_model(Task.EXTRACTION),
            system=SYSTEM_PROMPT,
            messages=[
                LLMMessage(
                    role="user",
                    content=f"Extrais les champs de cette facture.\n\nTexte du document :\n{text}",
                )
            ],
            response_schema=Invoice,
            max_tokens=8192,
        )
        response = self._llm_service.complete(request)

        if not isinstance(response.parsed, Invoice):
            raise ExtractionError("Le modèle n'a pas renvoyé de facture structurée")
        return ExtractionOutput(data=response.parsed, model=response.model)
