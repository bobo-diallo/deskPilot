from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_extractor, get_storage
from app.domains.documents.file_types import detect_media_type
from app.domains.documents.models import Document
from app.domains.documents.storage import FileStorage
from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.models import Extraction
from app.domains.extraction.ports import DocumentExtractor
from app.domains.extraction.service import ExtractionService
from app.domains.llm.errors import LLMInvalidOutputError, LLMRefusedError
from app.domains.transcription.models import Transcription

router = APIRouter(prefix="/extractions", tags=["extractions"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 Mo


class DocumentType(StrEnum):
    INVOICE = "invoice"


class TranscriptResult(BaseModel):
    text: str
    language: str
    duration_seconds: float
    model: str


class ExtractionResult(BaseModel):
    id: int
    document_id: int
    document_type: str
    status: str
    data: dict
    issues: list[dict]
    model: str
    transcript: TranscriptResult | None = None  # seulement pour un enregistrement


def _to_result(
    extraction: Extraction, transcription: Transcription | None = None
) -> ExtractionResult:
    return ExtractionResult(
        id=extraction.id,
        document_id=extraction.document_id,
        document_type=extraction.document_type,
        status=extraction.status,
        data=extraction.data,
        issues=extraction.issues,
        model=extraction.model,
        transcript=(
            TranscriptResult(
                text=transcription.text,
                language=transcription.language,
                duration_seconds=transcription.duration_seconds,
                model=transcription.model,
            )
            if transcription
            else None
        ),
    )


def _find_transcription(session: Session, extraction_id: int) -> Transcription | None:
    return session.scalars(
        select(Transcription).where(Transcription.extraction_id == extraction_id)
    ).first()


@router.post("")
def create_extraction(
    file: UploadFile,
    document_type: Annotated[DocumentType, Form()],
    extractor: Annotated[DocumentExtractor, Depends(get_extractor)],
    session: Annotated[Session, Depends(get_db_session)],
    storage: Annotated[FileStorage, Depends(get_storage)],
) -> ExtractionResult:
    # On lit un octet de plus que la limite pour savoir si le fichier la dépasse.
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (10 Mo maximum)")

    media_type = detect_media_type(content)
    if media_type is None:
        raise HTTPException(status_code=415, detail="Type de fichier non pris en charge")

    document = Document(filename=file.filename or "document", media_type=media_type)
    session.add(document)
    session.commit()
    storage.save(document.id, media_type, content)

    try:
        extraction = ExtractionService(extractor, session).extract_invoice(document, content)
    except LLMRefusedError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (ExtractionError, LLMInvalidOutputError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return _to_result(extraction, _find_transcription(session, extraction.id))


@router.get("/{extraction_id}")
def get_extraction(
    extraction_id: int, session: Annotated[Session, Depends(get_db_session)]
) -> ExtractionResult:
    extraction = session.get(Extraction, extraction_id)
    if extraction is None:
        raise HTTPException(status_code=404, detail="Extraction introuvable")
    return _to_result(extraction, _find_transcription(session, extraction.id))
