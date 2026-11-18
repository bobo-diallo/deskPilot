from app.domains.documents.file_types import is_audio
from app.domains.extraction.ports import DocumentExtractor, ExtractionOutput


class MediaTypeExtractor:
    """Aiguille chaque fichier vers le bon extracteur selon son type.

    La route d'envoi ne connaît qu'un seul `DocumentExtractor` : elle n'a pas à savoir
    si le fichier est un PDF, une image ou un enregistrement.
    """

    def __init__(self, visual: DocumentExtractor, audio: DocumentExtractor):
        self._visual = visual
        self._audio = audio

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput:
        extractor = self._audio if is_audio(media_type) else self._visual
        return extractor.extract(content, media_type)
