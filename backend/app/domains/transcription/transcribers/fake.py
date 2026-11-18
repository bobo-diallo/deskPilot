from app.domains.transcription.schemas import Transcript


class FakeTranscriber:
    """Transcripteur factice : renvoie toujours le même texte, sans modèle ni lenteur."""

    def __init__(self, text: str = "Texte factice", language: str = "fr", duration_seconds=1.0):
        self._text = text
        self._language = language
        self._duration_seconds = duration_seconds
        self.received: list[bytes] = []

    def transcribe(self, content: bytes, language: str | None = None) -> Transcript:
        self.received.append(content)
        return Transcript(
            text=self._text,
            language=self._language,
            duration_seconds=self._duration_seconds,
            model="fake",
        )
