from typing import Protocol

from app.domains.transcription.schemas import Transcript


class Transcriber(Protocol):
    """Contrat d'un transcripteur : de l'audio en entrée, du texte en sortie.

    Whisper local en est la première implémentation ; un service en ligne pourra
    s'y brancher plus tard sans toucher au reste (même idée que LLMProvider).
    """

    def transcribe(self, content: bytes, language: str | None = None) -> Transcript: ...
