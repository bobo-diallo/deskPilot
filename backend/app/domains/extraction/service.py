from sqlalchemy.orm import Session

from app.domains.documents.models import Document
from app.domains.extraction.models import Extraction, ExtractionStatus
from app.domains.extraction.ports import DocumentExtractor
from app.domains.extraction.validation import validate_invoice


class ExtractionService:
    """Extrait une facture, la contrôle, puis enregistre le résultat."""

    def __init__(self, extractor: DocumentExtractor, session: Session):
        self._extractor = extractor
        self._session = session

    def extract_invoice(self, document: Document, content: bytes) -> Extraction:
        output = self._extractor.extract(content, document.media_type)
        issues = validate_invoice(output.data)
        status = ExtractionStatus.NEEDS_REVIEW if issues else ExtractionStatus.VALIDATED

        extraction = Extraction(
            document_id=document.id,
            document_type="invoice",
            status=status.value,
            # mode="json" : dates en texte ISO et montants en texte exact (pas d'arrondi flottant)
            data=output.data.model_dump(mode="json"),
            issues=[
                {"code": issue.code.value, "field": issue.field, "message": issue.message}
                for issue in issues
            ],
            model=output.model,
        )
        self._session.add(extraction)
        self._session.commit()
        return extraction
