from dataclasses import dataclass
from typing import Protocol

from app.domains.extraction.schemas import Invoice


@dataclass(frozen=True)
class ExtractionOutput:
    data: Invoice
    model: str  # modèle (ou outil) qui a produit les données


class DocumentExtractor(Protocol):
    """Contrat d'un extracteur : lit un fichier et renvoie une facture structurée.

    Claude en est la première implémentation ; un extracteur local (Docling) pourra
    s'y brancher plus tard sans toucher au reste.
    """

    def extract(self, content: bytes, media_type: str) -> ExtractionOutput: ...
