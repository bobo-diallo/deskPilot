from sqlalchemy.orm import Session

from app.domains.documents.models import Document
from app.domains.extraction.models import Extraction, ExtractionStatus
from app.domains.extraction.ports import DocumentExtractor
from app.domains.extraction.validation import IssueCode, ValidationIssue, validate_invoice
from app.domains.transcription.models import Transcription


class ExtractionService:
    """Extrait une facture, la contrôle, puis enregistre le résultat."""

    def __init__(self, extractor: DocumentExtractor, session: Session):
        self._extractor = extractor
        self._session = session

    def extract_invoice(self, document: Document, content: bytes) -> Extraction:
        output = self._extractor.extract(content, document.media_type)
        issues = validate_invoice(output.data)
        if output.transcript is not None:
            # La voix se trompe sur les noms sans que les montants le montrent : relecture
            # obligatoire, quelle que soit la cohérence des chiffres.
            issues.append(
                ValidationIssue(
                    IssueCode.FROM_AUDIO, "Extraction issue d'une dictée : relecture obligatoire"
                )
            )
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
        self._session.flush()  # attribue l'id de l'extraction sans valider la transaction

        if output.transcript is not None:
            # Même transaction : l'extraction et sa transcription sont enregistrées ensemble
            self._session.add(
                Transcription(extraction_id=extraction.id, **output.transcript.model_dump())
            )
        self._session.commit()
        return extraction
