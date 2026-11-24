from dataclasses import dataclass
from typing import Protocol

from app.domains.extraction.schemas import Invoice
from app.domains.transcription.schemas import Transcript


@dataclass(frozen=True)
class ExtractionOutput:
    data: Invoice
    model: str  # modèle (ou outil) qui a produit les données
    transcript: Transcript | None = None  # présent seulement quand la source est de l'audio
    prompt_version: str | None = None  # version du prompt utilisée (None : extracteur sans prompt)


class DocumentExtractor(Protocol):
    """Contrat d'un extracteur : lit un fichier et renvoie une facture structurée.

    Claude en est la première implémentation ; un extracteur local (Docling) pourra
    s'y brancher plus tard sans toucher au reste.
    """

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput: ...
